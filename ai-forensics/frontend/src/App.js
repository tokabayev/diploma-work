import React from "react";
import FileUpload from "./components/FileUpload";
import { ToastContainer } from "react-toastify";
import "./App.css"; // Ensure this file is created for styling

function App() {
  return (
    <div className="app-container">
      <FileUpload />
      <ToastContainer position="top-right" autoClose={3000} />
    </div>
  );
}

export default App;
