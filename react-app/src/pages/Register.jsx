import { useState } from "react";
import { Link } from "react-router-dom";

import "./Forms.css";

const API_URL = import.meta.env.VITE_APP_BACKEND_ADDRESS; 

const LoginPage = () => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState(""); 
    const [resend, setResend] = useState(<p></p>); 


    const handleRegister = async (e) => {
        e.preventDefault();
        const response = await fetch(`${API_URL}/api/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password}),
        });
    
        const data = await response.json();
        
        if (response.status === 200) {
          setMessage(data.message);
          setResend(<p><Link to="/resend-verification">Resend verification email</Link></p>);
        } else {
            setMessage(data.detail || "Error");
        };
    };


    return (
        <div className="form-container">
         <h1>Register</h1>
            <form onSubmit={handleRegister}>
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
               
           
                
                <button type="submit">Register</button>
            </form>
            <p>{message}</p>
            {resend}
            <div>
                <p><Link to="/">Home</Link></p>
            </div>
        </div>
    );
};

export default LoginPage;