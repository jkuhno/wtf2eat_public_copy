import { useEffect, useState, useRef } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";

const API_URL = import.meta.env.VITE_APP_BACKEND_ADDRESS; 

const VerifyEmail = () => {
    const [searchParams] = useSearchParams();
    const [message, setMessage] = useState("Verifying...");
    const navigate = useNavigate();
    const token = searchParams.get("token");

    const hasRun = useRef(false); // Prevent double execution

    useEffect(() => {
        if (hasRun.current) return; // Prevent second run in Strict Mode
        hasRun.current = true;

        if (!token) {
            setMessage("Invalid verification link.");
            return;
        }

        navigate("/verify-email");

        const verifyEmail = async () => {
            try {
                const response = await fetch(`${API_URL}/api/verify-email?token=${token}`);
                const data = await response.json();

                if (response.ok) {
                    setMessage("Email verified! Redirecting to login...");
                    setTimeout(() => navigate("/login"), 3000);
                } else {
                    setMessage(data.detail + " Redirecting to re-send...");
                    setTimeout(() => navigate("/resend-verification"), 3000);
                }
            } catch (error) {
                setMessage("An error occurred. Please try again.");
            }
        };

        verifyEmail();
    }, []);

    return (
        <div>
            <h2>Email Verification</h2>
            <p>{message}</p>
            <p>
                <Link to="/">Home</Link>
            </p>
        </div>
    );
};

export default VerifyEmail;
