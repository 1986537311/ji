import React, { useContext, useState, useEffect } from "react";
import ModelCard from "./modelCard";
import Title from "../../components/Title";
import { Box, TextField, FormControl } from "@mui/material";
import { ApiContext } from "../../components/apiContext";

const LaunchModel = () => {
  let endPoint = useContext(ApiContext).endPoint;
  const [registrationData, setRegistrationData] = useState([]);
  const { isCallingApi, setIsCallingApi } = useContext(ApiContext);
  const { isUpdatingModel } = useContext(ApiContext);

  // States used for filtering
  const [searchTerm, setSearchTerm] = useState("");

  const handleChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const filter = (registration) => {
    if (
      !registration.model_name
        .toLowerCase()
        .includes(searchTerm.toLowerCase()) &&
      !registration.model_description
        .toLowerCase()
        .includes(searchTerm.toLowerCase())
    ) {
      return false;
    }
    return true;
  };

  const update = async () => {
    if (isCallingApi || isUpdatingModel) return;

    try {
      setIsCallingApi(true);

      const response = await fetch(`${endPoint}/v1/model_registrations/LLM`, {
        method: "GET",
      });

      const registrations = await response.json();

      const newRegistrationData = await Promise.all(
        registrations.map(async (registration) => {
          const detailResponse = await fetch(
            `${endPoint}/v1/model_registrations/LLM/${registration.model_name}`,
            {
              method: "GET",
            }
          );

          return await detailResponse.json();
        })
      );

      setRegistrationData(newRegistrationData);
      console.log(newRegistrationData);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsCallingApi(false);
    }
  };

  useEffect(() => {
    update();
    // eslint-disable-next-line
  }, []);

  const style = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    paddingLeft: "2rem",
    gridGap: "2rem 0rem",
  };

  return (
    <Box m="20px">
      <Title title="Launch Model" />
      <FormControl
        variant="outlined"
        margin="normal"
        sx={{ width: "100%", paddingBottom: "30px" }}
      >
        <TextField
          id="search"
          type="search"
          label="Search for model name and description"
          value={searchTerm}
          onChange={handleChange}
          size="small"
          sx={{ width: "95%", paddingBottom: "30px" }}
        />
      </FormControl>
      <div style={style}>
        {registrationData
          .filter((registration) => filter(registration))
          .map((filteredRegistration) => (
            <ModelCard url={endPoint} modelData={filteredRegistration} />
          ))}
      </div>
    </Box>
  );
};

export default LaunchModel;
