import React from "react";
import axios from "axios";
import styles from "./ComplianceTree.module.css";

interface Node {
  id: number;
  name: string;
  type: string;
  status: "PASS" | "FAIL";
  reason?: string;
  children: Node[];
}

interface ComplianceTreeProps {
  node: Node;
  onUpdate: () => void;
}

const ComplianceTree = ({ node, onUpdate }: ComplianceTreeProps) => {
  const handleOverride = async (
    nodeId: number,
    currentStatus: "PASS" | "FAIL"
  ) => {
    try {
      const newStatus = currentStatus === "PASS" ? "FAIL" : "PASS";
      await axios.put(
        `http://localhost:8000/override/${nodeId}?new_status=${newStatus}`
      );
      onUpdate();
    } catch (error) {
      console.error("Error updating status:", error);
      alert("Failed to update status");
    }
  };

  const renderNode = (node: Node, level: number = 0) => {
    // Check if node should fail based on children's status
    const hasFailingChild =
      node.children.length > 0 &&
      node.children.some(
        (child) =>
          child.status === "FAIL" ||
          (child.children.length > 0 &&
            child.children.some((grandChild) => grandChild.status === "FAIL"))
      );

    const effectiveStatus = hasFailingChild ? "FAIL" : node.status;
    const statusClass =
      effectiveStatus === "PASS" ? styles.statusPass : styles.statusFail;
    const buttonClass =
      node.status === "PASS"
        ? styles.overrideButtonPass
        : styles.overrideButtonFail;

    return (
      <div key={node.id} className={styles.nodeContainer}>
        <div className={styles.nodeWrapper}>
          <span className={styles.nodeName}>{node.name}</span>
          <span className={styles.nodeType}>[{node.type}] - Status: </span>
          <span className={statusClass}>{effectiveStatus}</span>
          <button
            onClick={() => handleOverride(node.id, node.status)}
            className={`${styles.overrideButton} ${buttonClass}`}
          >
            Override to {node.status === "PASS" ? "FAIL" : "PASS"}
          </button>
        </div>
        <div className={styles.childrenContainer}>
          {node.children.map((child) => renderNode(child, level + 1))}
        </div>
      </div>
    );
  };

  return renderNode(node);
};

export default ComplianceTree;
