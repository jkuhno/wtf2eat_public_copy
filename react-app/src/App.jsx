import { Routes, Route } from "react-router-dom";
import  LoginPage  from "./pages/Login";
import  RegisterPage  from "./pages/Register";
import  HomePage  from "./pages/Home";
import  PodiumUI  from "./pages/PodiumUI";
import ContactPage from "./pages/Contact";
import VerifyEmail from "./pages/VerifyEmail";
import ResendEmail from "./pages/ResendEmail";

import "./App.css";

import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider } from "./hooks/useAuth";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/resend-verification" element={<ResendEmail />} />
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <PodiumUI />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  );
};

export default App;