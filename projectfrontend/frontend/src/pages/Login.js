import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    setUsername("");
    setPassword("");
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://127.0.0.1:5000/login".trim(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (response.ok) {
        if (data.role === "admin") {
          navigate("/admin");
        } else {
          navigate("/tasks");
        }
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error("Error during login:", error);
      alert("Something went wrong. Try again.");
    }
  };

  return (
    <div style={{ maxWidth: "400px", margin: "50px auto" }}>
      <h2>Login</h2>
      <form onSubmit={handleLogin} autoComplete="off">
        {/* Hidden dummy fields to prevent autofill */}
        <input type="text" name="fakeusernameremembered" style={{ display: "none" }} />
        <input type="password" name="fakepasswordremembered" style={{ display: "none" }} />

        <div style={{ marginBottom: "10px" }}>
          <label>Username:</label>
          <input
            type="text"
            name="loginusername"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="off"
            style={{ width: "100%", padding: "8px", marginTop: "4px" }}
          />
        </div>

        <div style={{ marginBottom: "10px" }}>
          <label>Password:</label>
          <input
            type="password"
            name="loginpassword"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            style={{ width: "100%", padding: "8px", marginTop: "4px" }}
          />
        </div>

        <button type="submit" style={{ padding: "8px 16px" }}>
          Login
        </button>
      </form>

      <p style={{ marginTop: "10px" }}>
        Don't have an account? <Link to="/register">Go to Register</Link>
      </p>
    </div>
  );
}

export default Login;
