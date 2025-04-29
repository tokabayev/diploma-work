import React, { useState } from "react";
import axios from "axios";

const FileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [reportUrl, setReportUrl] = useState("");

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      const response = await axios.post("http://localhost:8000/analyze/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setReportUrl(response.data.pdf_report);
    } catch (error) {
      console.error("Error uploading file:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = `/reports/${reportUrl}`;
    link.download = reportUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ width: "900px", height: "850px", padding: "20px", background: "white", borderRadius: "10px", boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)" }}>
      <h2 style={{ textAlign: "center", fontSize: "22px", fontWeight: "bold" }}>Automated detection of unwanted vocabulary</h2>
      
      <div style={{ display: "flex", justifyContent: "center", marginBottom: "10px" }}>
        <button onClick={() => document.getElementById("fileInput").click()} style={{ padding: "10px 20px", marginRight: "25px", background: "#008080", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}>Upload</button>
        <button style={{ padding: "10px 20px", background: "#008080", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}>Edit</button>
      </div>

      <input id="fileInput" type="file" onChange={handleFileChange} style={{ display: "none" }} />
      <div style={{height:"200px", border: "2px dashed #ccc", padding: "20px", textAlign: "center", marginBottom: "10px" }}>
        {file ? file.name : "Drop your file here"}
      </div>
      <div style={{ textAlign: "center", marginBottom: "10px" }}>
      <button onClick={handleUpload} disabled={uploading} style={{ width: "20%", textAlign:"center", padding: "10px", background: "#008080", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", marginBottom: "10px" }}>
        {uploading ? "Uploading..." : "Analyze"}
      </button>
      </div>
      
      
      {reportUrl && (
        
        <div style={{ textAlign: "center", marginTop: "10px" }}>
          <div style={{ textAlign: "center", fontWeight: "bold" }}>Report</div>
          <div style={{ textAlign: "center", marginTop: "20px" }}>
      <button onClick={handleDownload} style={{ width: "20%", padding: "10px", background: "#008080", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", marginBottom: "10px" }}>Download Report<a href={`backend/${reportUrl}`} download style={{ color: "#008080", textDecoration: "underline" }}></a></button>
      </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
