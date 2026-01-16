import { useState, useEffect } from 'react';
import './index.css';

function App() {
    const [jobs, setJobs] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchJobs = async () => {
        try {
            const res = await fetch('https://localhost:8001/jobs');
            const data = await res.json();
            setJobs(data);
        } catch (e) {
            console.error("Failed to fetch jobs:", e);
        }
    };

    const fetchSchedules = async () => {
        try {
            const res = await fetch('https://localhost:8000/schedules', {
                headers: { 'X-API-KEY': 'master-secret-key' }
            });
            const data = await res.json();
            setSchedules(data);
        } catch (e) {
            console.error("Failed to fetch schedules:", e);
        }
    };

    useEffect(() => {
        fetchJobs();
        fetchSchedules();
        const interval = setInterval(() => {
            fetchJobs();
            fetchSchedules();
        }, 2000); // Real-time polling
        return () => clearInterval(interval);
    }, []);

    const createJob = async () => {
        setLoading(true);
        try {
            await fetch('https://localhost:8000/submit_intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-KEY': 'master-secret-key'
                },
                body: JSON.stringify({
                    task_type: 'web_task',
                    payload: {
                        message: `Task created at ${new Date().toLocaleTimeString()}`,
                        params: { a: 1, b: 2 }
                    },
                    priority: Math.floor(Math.random() * 10)
                })
            });
            // Immediate fetch after create
            setTimeout(fetchJobs, 500);
        } catch (e) {
            console.error("Failed to create job:", e);
            alert("Failed to submit intent to Model Service");
        } finally {
            setLoading(false);
        }
    };

    const createScriptJob = async () => {
        setLoading(true);
        try {
            await fetch('https://localhost:8000/submit_intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-KEY': 'master-secret-key'
                },
                body: JSON.stringify({
                    task_type: 'python_script',
                    payload: {
                        script_content: `import os\nprint("Hello from Remote Script!")\nprint(f"Secret: {os.environ.get('TEST_SECRET', 'NOT FOUND')}")\nprint(f"CWD: {os.getcwd()}")`,
                        requirements: [
                            { "type": "dir_exists", "path": "." }
                        ],
                        secrets: {
                            "TEST_SECRET": "TOP_SECRET_VALUE_123"
                        }
                    },
                    priority: 10
                })
            });
            setTimeout(fetchJobs, 500);
        } catch (e) {
            console.error("Failed to create script job:", e);
            alert("Failed to submit script");
        } finally {
            setLoading(false);
        }
    };

    const createSchedule = async () => {
        setLoading(true);
        try {
            await fetch('https://localhost:8000/schedules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-KEY': 'master-secret-key'
                },
                body: JSON.stringify({
                    name: `Heartbeat ${new Date().toLocaleTimeString()}`,
                    task_type: 'python_script',
                    interval_seconds: 10,
                    payload: {
                        script_content: 'import datetime\nprint(f"I am alive at {datetime.datetime.now()}")',
                        requirements: []
                    }
                })
            });
            setTimeout(fetchSchedules, 500);
        } catch (e) {
            alert("Failed to create schedule");
        } finally {
            setLoading(false);
        }
    };

    const deleteSchedule = async (id) => {
        if (!confirm("Delete schedule?")) return;
        try {
            await fetch(`https://localhost:8000/schedules/${id}`, {
                method: 'DELETE',
                headers: { 'X-API-KEY': 'master-secret-key' }
            });
            fetchSchedules();
        } catch (e) {
            alert("Delete failed");
        }
    };

    return (
        <div className="container">
            <header className="header">
                <h1>Orchestrator Control</h1>
                <div className="status-badge">
                    System: <span className="online">ONLINE</span>
                </div>
            </header>

            <main>
                <div className="controls">
                    <button
                        className="btn-primary"
                        onClick={createJob}
                        disabled={loading}
                    >
                        {loading ? 'Submitting...' : '+ New Intent'}
                    </button>
                    <button
                        className="btn-primary"
                        style={{ marginLeft: '10px', backgroundColor: '#e91e63' }}
                        onClick={createScriptJob}
                        disabled={loading}
                    >
                        {loading ? 'Submitting...' : '+ Test Script'}
                        {loading ? 'Submitting...' : '+ Test Script'}
                    </button>
                    <button
                        className="btn-primary"
                        style={{ marginLeft: '10px', backgroundColor: '#4caf50' }}
                        onClick={createSchedule}
                        disabled={loading}
                    >
                        + Add Heartbeat (10s)
                    </button>
                </div>

                <div className="section-title">Active Schedules</div>
                <div className="job-grid">
                    {schedules.length === 0 && <p className="empty-state">No active schedules.</p>}
                    {schedules.map(sch => (
                        <div key={sch.id} className="job-card status-scheduled" style={{ borderColor: '#4caf50' }}>
                            <div className="card-header">
                                <span className="guid">{sch.name}</span>
                                <button className="btn-sm" onClick={() => deleteSchedule(sch.id)}>🗑</button>
                            </div>
                            <div className="card-body">
                                <small>Next: {sch.next_run || 'Calculating...'}</small>
                                <pre>{JSON.stringify(sch.spec, null, 2)}</pre>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="section-title">Job History</div>

                <div className="job-grid">
                    {jobs.length === 0 && <p className="empty-state">No active jobs.</p>}
                    {jobs.map(job => (
                        <div key={job.guid} className={`job-card status-${job.status.toLowerCase()}`}>
                            <div className="card-header">
                                <span className="guid">{job.guid.split('-')[0]}...</span>
                                <span className={`badge ${job.status.toLowerCase()}`}>{job.status}</span>
                            </div>
                            <div className="card-body">
                                <pre>{JSON.stringify(job.payload, null, 2)}</pre>
                            </div>
                            {job.result && (
                                <div className="card-footer">
                                    <strong>Result:</strong>
                                    <pre>{JSON.stringify(job.result, null, 2)}</pre>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
}

export default App;
