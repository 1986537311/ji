import React, { useContext } from "react";
import { v1 as uuidv1 } from "uuid";
import { ApiContext } from "../../components/apiContext";

const ModelCard = ({ imgURL, serviceName, description, url, jsonData }) => {
  const { isCallingApi, setIsCallingApi } = useContext(ApiContext);
  const { isUpdatingModel } = useContext(ApiContext);

  const launchModel = (url, jsonData) => {
    setIsCallingApi(true);

    const uuid = uuidv1();
    const jsonDataWithID = {
      ...jsonData,
      model_uid: uuid,
      endpoint: url,
    };

    console.log("Sending request to: " + jsonDataWithID.endpoint);

    // First fetch request to initiate the model
    fetch(url + "/v1/models", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(jsonDataWithID),
    })
      .then((response) => {
        response.json();
        console.log("First");
      })
      .then((data) => {
        console.log("Firstdata");
        console.log(data);
        // Second fetch request to build the gradio page
        return fetch(url + "/v1/gradio/" + uuid, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(jsonDataWithID),
        });
      })
      .then((response) => {
        response.json();
        console.log("Second");
      })
      .then((data) => {
        console.log("Seconddata");
        console.log(data);
        window.open(url + "/" + uuid, "_blank", "noreferrer");
        setIsCallingApi(false);
      })
      .catch((error) => {
        console.error("Error:", error);
        setIsCallingApi(false);
      });
  };

  const styles = {
    card: {
      width: "280px",
      border: "1px solid #ddd",
      borderRadius: "20px",
      padding: "15px",
      background: "white",
    },
    img: {
      display: "block",
      margin: "0 auto",
      width: "180px",
      height: "180px",
      objectFit: "cover",
      borderRadius: "10px",
    },
    h2: {
      margin: "10px 10px",
      fontSize: "20px",
    },
    p: {
      fontSize: "14px",
      padding: "0px 0px 15px 0px",
    },
    button: {
      display: "block",
      padding: "10px 24px",
      margin: "0 auto",
      border: "none",
      borderRadius: "5px",
      cursor: "pointer",
      fontWeight: "bold",
    },
  };

  return (
    <div style={styles.card}>
      <img style={styles.img} src={imgURL} alt={serviceName} />
      <h2 style={styles.h2}>{serviceName}</h2>
      <p style={styles.p}>{description}</p>
      <button
        style={{
          ...styles.button,
          color: isCallingApi | isUpdatingModel ? "white" : "#ea580c",
          background:
            isCallingApi | isUpdatingModel
              ? "gray"
              : "linear-gradient(to bottom right, #ffedd5, #fdba74)",
        }}
        onClick={() => {
          launchModel(url, jsonData);
        }}
        disabled={isCallingApi | isUpdatingModel}
      >
        {isCallingApi | isUpdatingModel ? "Loading..." : "Launch"}
      </button>
    </div>
  );
};

export default ModelCard;
