import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import "./Forms.css";

const API_URL = import.meta.env.VITE_APP_BACKEND_ADDRESS; 

const ResendEmail = () => {
    const [email, setEmail] = useState("");
    const [message, setMessage] = useState(""); 

    const navigate = useNavigate();


    const handleResend = async (e) => {
        e.preventDefault();
        const response = await fetch(`${API_URL}/api/resend-verification`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
    
        const data = await response.json();
        
        if (response.status === 200) {
          setMessage(data.message);
          setTimeout(() => navigate("/"), 3000);
        } else {
          setMessage(data.detail || "Error");
        };
    };


    return (
        <div className="form-container">
         <h2>Resend verification email</h2>
            <form onSubmit={handleResend}>
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
                <button type="submit">Send verification</button>
            </form>
            <p>{message}</p>
            <div>
                <p><Link to="/">Home</Link></p>
            </div>
        </div>
    );
};

export default ResendEmail;