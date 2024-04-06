import { RocketLaunchOutlined, UndoOutlined } from '@mui/icons-material'
import DeleteIcon from '@mui/icons-material/Delete'
import {
  Box,
  Chip,
  CircularProgress,
  FormControl,
  Stack,
  TextField,
} from '@mui/material'
import IconButton from '@mui/material/IconButton'
import React, { useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ApiContext } from '../../../components/apiContext'
import fetcher from '../../../components/fetcher'
import cardStyles from './cardStyles'

const CARD_HEIGHT = 270
const CARD_WIDTH = 270

const AudioCard = ({
  url,
  modelData,
  is_custom = false,
}) => {
  const [modelUID, setModelUID] = useState('')
  const [hover, setHover] = useState(false)
  const [selected, setSelected] = useState(false)
  const [customDeleted, setCustomDeleted] = useState(false)
  const { setErrorMsg } = useContext(ApiContext)
  const { isCallingApi, setIsCallingApi } = useContext(ApiContext)
  const { isUpdatingModel } = useContext(ApiContext)
  const navigate = useNavigate()
  // UseEffects for parameter selection, change options based on previous selections
  useEffect(() => {}, [modelData])

  const launchModel = (url) => {
    if (isCallingApi || isUpdatingModel) {
      return
    }

    setIsCallingApi(true)

    const modelDataWithID = {
      model_uid: modelUID.trim() === '' ? null : modelUID.trim(),
      model_name: modelData.model_name,
      model_type: 'audio',
    }

    // First fetcher request to initiate the model
    fetcher(url + '/v1/models', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(modelDataWithID),
    })
      .then((response) => {
        if (!response.ok) {
          // Assuming the server returns error details in JSON format
          response.json().then((errorData) => {
            setErrorMsg(
              `Server error: ${response.status} - ${
                errorData.detail || 'Unknown error'
              }`
            )
          })
        } else {
          navigate('/running_models')
        }
        setIsCallingApi(false)
      })
      .catch((error) => {
        console.error('Error:', error)
        setIsCallingApi(false)
      })
  }

  const styles = {
    ...cardStyles(CARD_WIDTH, CARD_HEIGHT)
  }

  const handeCustomDelete = (e) => {
    e.stopPropagation()
    fetcher(url + `/v1/model_registrations/audio/${modelData.model_name}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(() => setCustomDeleted(true))
      .catch(console.error)
  }

  // Set two different states based on mouse hover
  return (
    <Box
      style={hover ? styles.containerSelected : styles.container}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={() => {
        if (!selected && !customDeleted) {
          setSelected(true)
        }
      }}
    >
      {/* First state: show description page */}
      <Box style={styles.descriptionCard}>
        <div style={styles.titleContainer}>
          {is_custom && (
            <Stack
              direction="row"
              justifyContent="space-evenly"
              alignItems="center"
              spacing={1}
            >
              <h2 style={styles.h2}>{modelData.model_name}</h2>
              <IconButton
                aria-label="delete"
                onClick={handeCustomDelete}
                disabled={customDeleted}
              >
                <DeleteIcon />
              </IconButton>
            </Stack>
          )}
          {!is_custom && <h2 style={styles.h2}>{modelData.model_name}</h2>}
          <Stack
            spacing={1}
            direction="row"
            useFlexGap
            flexWrap="wrap"
            sx={{ marginLeft: 1 }}
          >
            {(() => {
              return (
                <Chip
                  label={modelData.model_family}
                  variant="outlined"
                  size="small"
                />
              )
            })()}
            {(() => {
              if (modelData.cache_status) {
                return <Chip label="Cached" variant="outlined" size="small" />
              }
            })()}
            {(() => {
              if (is_custom && customDeleted) {
                return <Chip label="Deleted" variant="outlined" size="small" />
              }
            })()}
          </Stack>
        </div>
        {!selected && hover && (
          <p style={styles.instructionText}>
            Click with mouse to launch the model
          </p>
        )}
      </Box>
      {/* Second state: show parameter selection page */}
      <Box
        style={
          selected
            ? { ...styles.parameterCard, ...styles.slideIn }
            : { ...styles.parameterCard, ...styles.slideOut }
        }
      >
        <h2 style={styles.h2}>{modelData.model_name}</h2>
        <FormControl variant="outlined" margin="normal" fullWidth>
          <TextField
            variant="outlined"
            value={modelUID}
            label="(Optional) Model UID, model name by default"
            onChange={(e) => setModelUID(e.target.value)}
          />
        </FormControl>
        <Box style={styles.buttonsContainer}>
          <button
            title="Launch Audio"
            style={styles.buttonContainer}
            onClick={() => launchModel(url, modelData)}
            disabled={isCallingApi || isUpdatingModel || !modelData}
          >
            {(() => {
              if (isCallingApi || isUpdatingModel) {
                return (
                  <Box
                    style={{ ...styles.buttonItem, backgroundColor: '#f2f2f2' }}
                  >
                    <CircularProgress
                      size="20px"
                      sx={{
                        color: '#000000',
                      }}
                    />
                  </Box>
                )
              } else if (!modelData) {
                return (
                  <Box
                    style={{ ...styles.buttonItem, backgroundColor: '#f2f2f2' }}
                  >
                    <RocketLaunchOutlined size="20px" />
                  </Box>
                )
              } else {
                return (
                  <Box style={styles.buttonItem}>
                    <RocketLaunchOutlined color="#000000" size="20px" />
                  </Box>
                )
              }
            })()}
          </button>
          <button
            title="Launch Audio"
            style={styles.buttonContainer}
            onClick={() => setSelected(false)}
          >
            <Box style={styles.buttonItem}>
              <UndoOutlined color="#000000" size="20px" />
            </Box>
          </button>
        </Box>
      </Box>
    </Box>
  )
}

export default AudioCard
