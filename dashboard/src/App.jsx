import { BrowserRouter } from 'react-router-dom';
import AppRoutes from './AppRoutes';
import './index.css';

function App() {
    console.log("[DEBUG] App.jsx: Rendering App Component");
    return (
        <BrowserRouter>
            <AppRoutes />
        </BrowserRouter>
    );
}

export default App;
