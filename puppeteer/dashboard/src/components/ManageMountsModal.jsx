import { useState, useEffect } from 'react';
import { authenticatedFetch } from '../auth';

const ManageMountsModal = ({ onClose }) => {
    const [mounts, setMounts] = useState([]);
    const [newName, setNewName] = useState('');
    const [newPath, setNewPath] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchMounts = async () => {
        try {
            const res = await authenticatedFetch('https://localhost:8001/config/mounts');
            if (res.ok) {
                setMounts(await res.json());
            } else {
                setError("Failed to load mounts");
            }
        } catch (e) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMounts();
    }, []);

    const handleSave = async (updatedMounts) => {
        try {
            const res = await authenticatedFetch('https://localhost:8001/config/mounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mounts: updatedMounts })
            });

            if (!res.ok) {
                const err = await res.json();
                setError(err.detail || "Failed to save");
                return false;
            }
            setMounts(updatedMounts);
            setNewName('');
            setNewPath('');
            setError(null);
            return true;
        } catch (e) {
            setError(e.message);
            return false;
        }
    };

    const handleAdd = () => {
        if (!newName || !newPath) return;
        if (!/^[a-zA-Z0-9_]+$/.test(newName)) {
            setError("Name must be alphanumeric (underscores allowed).");
            return;
        }
        // Check duplicate
        if (mounts.some(m => m.name === newName)) {
            setError("Mount name already exists.");
            return;
        }

        const newList = [...mounts, { name: newName, path: newPath }];
        handleSave(newList);
    };

    const handleDelete = (name) => {
        if (!window.confirm(`Delete mount '${name}'? Nodes must be redeployed.`)) return;
        const newList = mounts.filter(m => m.name !== name);
        handleSave(newList);
    };

    if (loading) return <div className="modal-overlay">Loading...</div>;

    return (
        <div className="modal-overlay">
            <div className="modal" style={{ maxWidth: '700px' }}>
                <h2>Network Mounts</h2>

                <div className="alert-box warning" style={{ marginBottom: '15px', padding: '10px', background: '#fff3cd', color: '#856404', borderRadius: '4px' }}>
                    ⚠️ <b>Warning:</b> Adding or Removing mounts requires re-running the Installer on all Nodes.
                </div>

                {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

                <table style={{ width: '100%', marginBottom: '20px', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ background: '#eee' }}>
                            <th style={{ padding: '8px', textAlign: 'left' }}>Name (Internal)</th>
                            <th style={{ padding: '8px', textAlign: 'left' }}>Path (UNC/Host)</th>
                            <th style={{ padding: '8px' }}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {mounts.map(m => (
                            <tr key={m.name} style={{ borderBottom: '1px solid #ddd' }}>
                                <td style={{ padding: '8px' }}>{m.name}</td>
                                <td style={{ padding: '8px' }}>{m.path}</td>
                                <td style={{ padding: '8px', textAlign: 'center' }}>
                                    <button onClick={() => handleDelete(m.name)} className="btn danger small">🗑️</button>
                                </td>
                            </tr>
                        ))}
                        {mounts.length === 0 && <tr><td colSpan="3" style={{ padding: '10px', textAlign: 'center', fontStyle: 'italic' }}>No mounts configured.</td></tr>}
                    </tbody>
                </table>

                <div style={{ background: '#f9f9f9', padding: '15px', borderRadius: '5px', marginBottom: '20px' }}>
                    <h4>Add New Mount</h4>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <input
                            placeholder="Name (e.g. projects)"
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                            style={{ flex: 1, padding: '8px' }}
                        />
                        <input
                            placeholder="Host Path (e.g. \\server\share or C:\Data)"
                            value={newPath}
                            onChange={e => setNewPath(e.target.value)}
                            style={{ flex: 2, padding: '8px' }}
                        />
                        <button onClick={handleAdd} className="btn primary">Add</button>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button onClick={onClose} className="btn">Close</button>
                </div>
            </div>
        </div>
    );
};

export default ManageMountsModal;
