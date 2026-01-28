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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-zinc-900 rounded-lg shadow-xl w-full max-w-2xl p-6">
                <h2 className="text-xl font-bold mb-4">Network Mounts</h2>

                <div className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 p-3 rounded mb-4 text-sm">
                    ⚠️ <b>Warning:</b> Adding or Removing mounts requires re-running the Installer on all Nodes.
                </div>

                {error && <div className="text-red-500 mb-2">{error}</div>}

                <div className="overflow-x-auto mb-6">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-100 dark:bg-zinc-800">
                            <tr>
                                <th className="p-2">Name (Internal)</th>
                                <th className="p-2">Path (UNC/Host)</th>
                                <th className="p-2 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {mounts.map(m => (
                                <tr key={m.name} className="border-b dark:border-zinc-800 hover:bg-gray-50 dark:hover:bg-zinc-800/50">
                                    <td className="p-2">{m.name}</td>
                                    <td className="p-2 font-mono text-xs">{m.path}</td>
                                    <td className="p-2 text-center">
                                        <button onClick={() => handleDelete(m.name)} className="text-red-500 hover:text-red-700">🗑️</button>
                                    </td>
                                </tr>
                            ))}
                            {mounts.length === 0 && (
                                <tr>
                                    <td colSpan="3" className="p-4 text-center italic text-gray-500">No mounts configured.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="bg-gray-50 dark:bg-zinc-800/50 p-4 rounded mb-6">
                    <h4 className="font-semibold mb-2">Add New Mount</h4>
                    <div className="flex gap-2">
                        <input
                            placeholder="Name (e.g. projects)"
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                            className="flex-1 p-2 border rounded dark:bg-zinc-900 dark:border-zinc-700"
                        />
                        <input
                            placeholder="Host Path (e.g. \\server\share)"
                            value={newPath}
                            onChange={e => setNewPath(e.target.value)}
                            className="flex-[2] p-2 border rounded dark:bg-zinc-900 dark:border-zinc-700"
                        />
                        <button onClick={handleAdd} className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Add</button>
                    </div>
                </div>

                <div className="flex justify-end">
                    <button onClick={onClose} className="px-4 py-2 text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white">Close</button>
                </div>
            </div>
        </div>
    );
};

export default ManageMountsModal;
