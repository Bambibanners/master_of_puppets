import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../auth';

const AddNodeModal = ({ onClose }) => {
    const [token, setToken] = useState('');
    const [count, setCount] = useState(1);
    const [loading, setLoading] = useState(true);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        // Generate Token on Mount
        const genToken = async () => {
            try {
                const res = await authenticatedFetch('https://localhost:8001/admin/generate-token', {
                    method: 'POST'
                });
                if (res.ok) {
                    const data = await res.json();
                    setToken(data.token);
                }
            } catch (e) {
                console.error("Token Gen Failed", e);
            } finally {
                setLoading(false);
            }
        };
        genToken();
    }, []);

    const handleCopy = () => {
        const snippet = `.\\install_node.ps1 -ServerUrl "https://host.containers.internal:8001" -JoinToken "${token}" -Count ${count}`;
        navigator.clipboard.writeText(snippet);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownload = () => {
        // Direct download link to the API
        window.location.href = "https://localhost:8001/api/installer";
    };

    if (loading) return <div className="modal-overlay">Loading...</div>;

    return (
        <div className="modal-overlay">
            <div className="modal" style={{ maxWidth: '600px' }}>
                <h2>Deploy New Nodes</h2>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Step 1: Download Installer</label>
                    <button onClick={handleDownload} className="btn primary">
                        ⬇️ Download install_node.ps1
                    </button>
                    <p style={{ fontSize: '0.9em', color: '#aaa', marginTop: '5px' }}>
                        Save this to a folder on your Windows machine.
                    </p>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Step 2: How many nodes?</label>
                    <input
                        type="number"
                        min="1"
                        max="20"
                        value={count}
                        onChange={(e) => setCount(parseInt(e.target.value) || 1)}
                        style={{ padding: '8px', width: '100px' }}
                    />
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '5px' }}>Step 3: Run Command (Admin PowerShell)</label>
                    <div className="code-block" style={{
                        background: '#333',
                        padding: '15px',
                        borderRadius: '5px',
                        fontFamily: 'monospace',
                        wordBreak: 'break-all',
                        position: 'relative'
                    }}>
                        {`.\\install_node.ps1 -ServerUrl "https://host.containers.internal:8001" -JoinToken "${token}" -Count ${count}`}
                        <button
                            onClick={handleCopy}
                            style={{
                                position: 'absolute',
                                right: '10px',
                                top: '10px',
                                background: copied ? '#4caf50' : '#555',
                                border: 'none',
                                color: 'white',
                                padding: '5px 10px',
                                cursor: 'pointer'
                            }}
                        >
                            {copied ? 'Copied!' : 'Copy'}
                        </button>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                    <button onClick={onClose} className="btn">Close</button>
                </div>
            </div>
        </div>
    );
};

export default AddNodeModal;
