import React, { useEffect, useState } from "react";
import axios from "axios";
import ComplianceTree from "./components/ComplianceTree";

interface Node {
  id: number;
  name: string;
  type: string;
  status: "PASS" | "FAIL";
  reason?: string;
  children: Node[];
}

const App = () => {
  const [rootNode, setRootNode] = useState<Node | null>(null);

  const fetchTree = async () => {
    try {
      const response = await axios.get("http://localhost:8000/");
      setRootNode(response.data);
      localStorage.setItem("treeRootId", response.data.id.toString());
    } catch (error) {
      console.error("Error fetching tree:", error);
    }
  };

  const handleTreeUpdate = async () => {
    try {
      const rootId = localStorage.getItem("treeRootId");
      if (rootId) {
        const response = await axios.get(
          `http://localhost:8000/node/${rootId}`
        );
        setRootNode(response.data);
      }
    } catch (error) {
      console.error("Error updating tree:", error);
    }
  };

  // Fetch initial tree data
  useEffect(() => {
    if (!rootNode) {
      fetchTree();
    }
  }, []);

  if (!rootNode) return <p>Loading...</p>;

  return (
    <div className="App">
      <h1>Compliance Analysis Tree</h1>
      <ComplianceTree node={rootNode} onUpdate={handleTreeUpdate} />
    </div>
  );
};

export default App;
