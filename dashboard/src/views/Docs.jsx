import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../auth';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Docs = () => {
    const [docs, setDocs] = useState([]);
    const [selectedDoc, setSelectedDoc] = useState(null);
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(false);

    // Allow linking to specific doc via ?page=filename.md
    const [searchParams, setSearchParams] = useSearchParams();

    useEffect(() => {
        const fetchList = async () => {
            try {
                const res = await authenticatedFetch('https://localhost:8001/api/docs');
                if (res.ok) {
                    const data = await res.json();
                    setDocs(data);

                    // Auto-select from URL or first item
                    const page = searchParams.get('page');
                    if (page) {
                        const found = data.find(d => d.filename === page);
                        if (found) loadDoc(found);
                    } else if (data.length > 0) {
                        loadDoc(data[0]);
                    }
                } else {
                    console.error("Failed to fetch docs list:", res.status);
                }
            } catch (e) {
                console.error("Failed to load docs list", e);
            }
        };
        fetchList();
    }, []);

    const loadDoc = async (doc) => {
        setSelectedDoc(doc);
        setLoading(true);
        setSearchParams({ page: doc.filename });

        try {
            const res = await authenticatedFetch(`https://localhost:8001/api/docs/${doc.filename}`);
            if (res.ok) {
                const data = await res.json();
                setContent(data.content);
            } else {
                setContent(`# Error\nFailed to load document: ${res.status}`);
            }
        } catch (e) {
            setContent(`# Error\n${e.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', height: 'calc(100vh - 40px)', gap: '20px' }}>
            {/* Sidebar */}
            <div style={{ width: '250px', borderRight: '1px solid #ddd', paddingRight: '20px' }}>
                <h3>Documentation</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    {docs.map(doc => (
                        <button
                            key={doc.filename}
                            onClick={() => loadDoc(doc)}
                            className={`btn ${selectedDoc?.filename === doc.filename ? 'primary' : ''}`}
                            style={{
                                textAlign: 'left',
                                width: '100%',
                                border: 'none',
                                background: selectedDoc?.filename === doc.filename ? '#e91e63' : 'transparent',
                                color: selectedDoc?.filename === doc.filename ? 'white' : '#aaa',
                                cursor: 'pointer',
                                padding: '10px',
                                borderRadius: '4px'
                            }}
                        >
                            {doc.title || doc.filename}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content Area */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px', backgroundColor: '#1e1e1e', borderRadius: '8px' }}>
                {loading ? (
                    <div style={{ padding: '20px' }}>Loading...</div>
                ) : (
                    <div className="markdown-body" style={{ padding: '20px', color: '#ddd' }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Docs;
