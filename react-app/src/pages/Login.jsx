import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth} from "../hooks/useAuth";

import "./Forms.css";

const API_URL = import.meta.env.VITE_APP_BACKEND_ADDRESS; 

const LoginPage = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const { login } = useAuth();


    const handleLogin = async (e) => {
        e.preventDefault();
        const response = await fetch(`${API_URL}/api/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
    
        const data = await response.json();
        if (data.access_token) {
          localStorage.setItem("token", data.access_token); // Store token
          await login({ email });
          setMessage("Login successful! Redirecting...");
        } else {
            setMessage(data.detail || "Error");
        }
      };


    return (
        <div className="form-container">
         <h1>Login</h1>
            <form onSubmit={handleLogin}>
                <div>
                  <label htmlFor="email">Email:</label>
                  <input
                    className="input-field"
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                </div>
                <div>
                    <label htmlFor="password">Password:</label>
                    <input
                        className="input-field"
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                />
                </div>
                <button type="submit">Login 🔑</button>
            </form>
            <p>{message}</p>
            <div>
                <p>No account yet? Sign up  <Link to="/register">here</Link>.</p>
            </div>
            <div>
                <p><Link to="/">Home</Link></p>
            </div>
        </div>
    );
};

export default LoginPage;