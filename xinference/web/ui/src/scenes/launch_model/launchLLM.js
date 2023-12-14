import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from '@mui/material'
import React, { useContext, useEffect, useState } from 'react'

import { ApiContext } from '../../components/apiContext'
import ModelCard from './modelCard'

const LaunchLLM = ({ gpuAvailable }) => {
  let endPoint = useContext(ApiContext).endPoint
  const [registrationData, setRegistrationData] = useState([])
  const { isCallingApi, setIsCallingApi } = useContext(ApiContext)
  const { isUpdatingModel } = useContext(ApiContext)

  // States used for filtering
  const [searchTerm, setSearchTerm] = useState('')

  const [modelAbility, setModelAbility] = useState('all')

  const handleChange = (event) => {
    setSearchTerm(event.target.value)
  }

  const handleAbilityChange = (event) => {
    setModelAbility(event.target.value)
  }

  const filter = (registration) => {
    if (!registration || typeof searchTerm !== 'string') return false
    const modelName = registration.model_name
      ? registration.model_name.toLowerCase()
      : ''
    const modelDescription = registration.model_description
      ? registration.model_description.toLowerCase()
      : ''

    if (
      !modelName.includes(searchTerm.toLowerCase()) &&
      !modelDescription.includes(searchTerm.toLowerCase())
    ) {
      return false
    }
    if (modelAbility && modelAbility !== 'all') {
      if (registration.model_ability.indexOf(modelAbility) < 0) {
        return false
      }
    }
    return true
  }

  const update = async () => {
    if (isCallingApi || isUpdatingModel) return

    try {
      setIsCallingApi(true)

      const response = await fetch(
        `${endPoint}/v1/model_registrations/LLM?detailed=true`,
        {
          method: 'GET',
        }
      )

      const registrations = await response.json()
      const builtinRegistrations = registrations.filter((v) => v.is_builtin)

      setRegistrationData(builtinRegistrations)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setIsCallingApi(false)
    }
  }

  useEffect(() => {
    update().catch(console.error)
  }, [])

  const style = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    paddingLeft: '2rem',
    gridGap: '2rem 0rem',
  }

  return (
    <Box m="20px">
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '150px 1fr',
          columnGap: '20px',
          margin: '30px 2rem',
        }}
      >
        <FormControl variant="outlined" margin="normal">
          <InputLabel id="ability-select-label">Model Ability</InputLabel>
          <Select
            id="ability"
            labelId="ability-select-label"
            label="Model Ability"
            onChange={handleAbilityChange}
            value={modelAbility}
            size="small"
            sx={{ width: '150px' }}
          >
            <MenuItem value="all">all</MenuItem>
            <MenuItem value="generate">generate</MenuItem>
            <MenuItem value="chat">chat</MenuItem>
          </Select>
        </FormControl>
        <FormControl variant="outlined" margin="normal">
          <TextField
            id="search"
            type="search"
            label="Search for model name and description"
            value={searchTerm}
            onChange={handleChange}
            size="small"
          />
        </FormControl>
      </div>
      <div style={style}>
        {registrationData
          .filter((registration) => filter(registration))
          .map((filteredRegistration) => (
            <ModelCard
              url={endPoint}
              modelData={filteredRegistration}
              gpuAvailable={gpuAvailable}
            />
          ))}
      </div>
    </Box>
  )
}

export default LaunchLLM
