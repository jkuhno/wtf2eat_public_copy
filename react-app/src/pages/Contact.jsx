import { useState } from "react";
import { Link } from "react-router-dom";
import Turnstile from "react-turnstile";

import "./Forms.css";

const API_URL = import.meta.env.VITE_APP_BACKEND_ADDRESS; 
const CF_TURNSTILE_SITE = import.meta.env.VITE_CF_TURNSTILE_SITE;


const ContactPage = () => {
    const [email, setEmail] = useState("");
    const [contact, setContact] = useState(""); 
    const [message, setMessage] = useState(""); 
    const [captchaToken, setCaptchaToken] = useState(null);


    const handleSend = async (e) => {
        e.preventDefault();

        if (!captchaToken) {
            setMessage("Please complete the CAPTCHA verification.");
            return;
        }

        const response = await fetch(`${API_URL}/api/contact`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({email, contact, captcha: captchaToken}),
        });
    
        const data = await response.json();

        
        if (data.message === "Email sent successfully") {
          setMessage("Message sent You will be contacted if requested.");
        } else {
            setMessage(data.detail || "Error");
        };
    };


    return (
        <div className="form-container">
         <h1>Contact form</h1>
            <form onSubmit={handleSend}>
                <div>
                  <label htmlFor="email">* Email:</label>
                  <input
                    className="input-field"
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
                </div>
                <div>
                    <label htmlFor="contact">* Message:</label>
                    <textarea
                        className="input-field"
                        id="contact"
                        type="text"
                        rows="10"
                        required
                        value={contact}
                        onChange={(e) => setContact(e.target.value)}
                />
                </div>

                 {/* Cloudflare Turnstile CAPTCHA */}
                 <Turnstile
                    sitekey={CF_TURNSTILE_SITE}// Replace with your actual Turnstile site key
                    onVerify={(token) => setCaptchaToken(token)} // Store the token when verified
                />

                <p> * Required fields </p>
               
                <button type="submit">Send</button>
            </form>
            <p>{message}</p>
            <div>
                <p><Link to="/">Home</Link></p>
            </div>
        </div>
    );
};

export default ContactPage;