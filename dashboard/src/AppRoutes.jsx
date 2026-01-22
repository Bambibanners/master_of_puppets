import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './views/Login';
import Dashboard from './views/Dashboard';
import Nodes from './views/Nodes';
import Jobs from './views/Jobs';
import JobDefinitions from './views/JobDefinitions';
import Signatures from './views/Signatures';
import Admin from './views/Admin';
import Docs from './views/Docs';
import MainLayout from './layouts/MainLayout';
import { getUser } from './auth';

const PrivateRoute = ({ children }) => {
    const user = getUser();
    return user ? children : <Navigate to="/login" />;
};

const AppRoutes = () => {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={<PrivateRoute><MainLayout /></PrivateRoute>}>
                <Route index element={<Dashboard />} />
                <Route path="nodes" element={<Nodes />} />
                <Route path="jobs" element={<Jobs />} />
                <Route path="scheduled-jobs" element={<JobDefinitions />} />
                <Route path="signatures" element={<Signatures />} />
                <Route path="admin" element={<Admin />} />
                <Route path="docs" element={<Docs />} /> {/* Added Docs route */}
            </Route>
        </Routes>
    );
};

export default AppRoutes;
