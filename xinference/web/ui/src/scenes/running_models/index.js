import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined'
import OpenInBrowserOutlinedIcon from '@mui/icons-material/OpenInBrowserOutlined'
import { TabContext, TabList, TabPanel } from '@mui/lab'
import { Box, Stack, Tab } from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import React, { useContext, useEffect, useState } from 'react'

import { ApiContext } from '../../components/apiContext'
import Title from '../../components/Title'

const RunningModels = () => {
  const [tabValue, setTabValue] = React.useState('1')
  const [llmData, setLlmData] = useState([])
  const [embeddingModelData, setEmbeddingModelData] = useState([])
  const [imageModelData, setImageModelData] = useState([])
  const [rerankModelData, setRerankModelData] = useState([])
  const { isCallingApi, setIsCallingApi } = useContext(ApiContext)
  const { isUpdatingModel, setIsUpdatingModel } = useContext(ApiContext)
  const endPoint = useContext(ApiContext).endPoint

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue)
  }

  const update = (isCallingApi) => {
    if (isCallingApi) {
      setLlmData([{ id: 'Loading, do not refresh page...', url: 'IS_LOADING' }])
      setEmbeddingModelData([
        { id: 'Loading, do not refresh page...', url: 'IS_LOADING' },
      ])
      setImageModelData([
        { id: 'Loading, do not refresh page...', url: 'IS_LOADING' },
      ])
      setRerankModelData([
        { id: 'Loading, do not refresh page...', url: 'IS_LOADING' },
      ])
    } else {
      setIsUpdatingModel(true)
      fetch(`${endPoint}/v1/models/`, {
        method: 'GET',
      })
        .then((response) => response.json())
        .then((data) => {
          const newLlmData = []
          const newEmbeddingModelData = []
          const newImageModelData = []
          const newRerankModelData = []
          Object.entries(data).forEach(([key, value]) => {
            let newValue = {
              ...value,
              id: key,
              url: key,
            }
            if (newValue.model_type === 'LLM') {
              newLlmData.push(newValue)
            } else if (newValue.model_type === 'embedding') {
              newEmbeddingModelData.push(newValue)
            } else if (newValue.model_type === 'image') {
              newImageModelData.push(newValue)
            } else if (newValue.model_type === 'rerank') {
              newRerankModelData.push(newValue)
            }
          })
          setLlmData(newLlmData)
          setEmbeddingModelData(newEmbeddingModelData)
          setImageModelData(newImageModelData)
          setRerankModelData(newRerankModelData)
          setIsUpdatingModel(false)
        })
        .catch((error) => {
          console.error('Error:', error)
          setIsUpdatingModel(false)
        })
    }
  }

  useEffect(() => {
    update(isCallingApi)
    // eslint-disable-next-line
  }, [isCallingApi])

  const llmColumns = [
    {
      field: 'id',
      headerName: 'ID',
      flex: 1,
      minWidth: 250,
    },
    {
      field: 'model_name',
      headerName: 'Name',
      flex: 1,
    },
    {
      field: 'address',
      headerName: 'Address',
      flex: 1,
    },
    {
      field: 'accelerators',
      headerName: 'GPU Indexes',
      flex: 1,
    },
    {
      field: 'model_size_in_billions',
      headerName: 'Size',
      flex: 1,
    },
    {
      field: 'quantization',
      headerName: 'Quantization',
      flex: 1,
    },
    {
      field: 'url',
      headerName: 'Actions',
      flex: 1,
      minWidth: 200,
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
      renderCell: ({ row }) => {
        const url = row.url
        const openUrl = `${endPoint}/` + url
        const closeUrl = `${endPoint}/v1/models/` + url
        const gradioUrl = `${endPoint}/v1/ui/` + url

        if (url === 'IS_LOADING') {
          return <div></div>
        }

        return (
          <Box
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'left',
              alignItems: 'left',
            }}
          >
            <button
              title="Launch Web UI"
              style={{
                borderWidth: '0px',
                backgroundColor: 'transparent',
                paddingLeft: '0px',
                paddingRight: '10px',
              }}
              onClick={() => {
                if (isCallingApi || isUpdatingModel) {
                  // Make sure no ongoing call
                  return
                }

                setIsCallingApi(true)

                fetch(openUrl, {
                  method: 'HEAD',
                })
                  .then((response) => {
                    if (response.status === 404) {
                      // If web UI doesn't exist (404 Not Found)
                      console.log('UI does not exist, creating new...')
                      return fetch(gradioUrl, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                          model_type: row.model_type,
                          model_name: row.model_name,
                          model_size_in_billions: row.model_size_in_billions,
                          model_format: row.model_format,
                          quantization: row.quantization,
                          context_length: row.context_length,
                          model_ability: row.model_ability,
                          model_description: row.model_description,
                          model_lang: row.model_lang,
                        }),
                      })
                        .then((response) => response.json())
                        .then(() =>
                          window.open(openUrl, '_blank', 'noopener noreferrer')
                        )
                        .finally(() => setIsCallingApi(false))
                    } else if (response.ok) {
                      // If web UI does exist
                      console.log('UI exists, opening...')
                      window.open(openUrl, '_blank', 'noopener noreferrer')
                      setIsCallingApi(false)
                    } else {
                      // Other HTTP errors
                      console.error(
                        `Unexpected response status: ${response.status}`
                      )
                      setIsCallingApi(false)
                    }
                  })
                  .catch((error) => {
                    console.error('Error:', error)
                    setIsCallingApi(false)
                  })
              }}
            >
              <Box
                width="40px"
                m="0 auto"
                p="5px"
                display="flex"
                justifyContent="center"
                borderRadius="4px"
                style={{
                  border: '1px solid #e5e7eb',
                  borderWidth: '1px',
                  borderColor: '#e5e7eb',
                }}
              >
                <OpenInBrowserOutlinedIcon />
              </Box>
            </button>
            <button
              title="Terminate Model"
              style={{
                borderWidth: '0px',
                backgroundColor: 'transparent',
                paddingLeft: '0px',
                paddingRight: '10px',
              }}
              onClick={() => {
                if (isCallingApi || isUpdatingModel) {
                  return
                }
                setIsCallingApi(true)
                fetch(closeUrl, {
                  method: 'DELETE',
                })
                  .then((response) => {
                    response.json()
                  })
                  .then(() => {
                    setIsCallingApi(false)
                  })
                  .catch((error) => {
                    console.error('Error:', error)
                    setIsCallingApi(false)
                  })
              }}
            >
              <Box
                width="40px"
                m="0 auto"
                p="5px"
                display="flex"
                justifyContent="center"
                borderRadius="4px"
                style={{
                  border: '1px solid #e5e7eb',
                  borderWidth: '1px',
                  borderColor: '#e5e7eb',
                }}
              >
                <DeleteOutlineOutlinedIcon />
              </Box>
            </button>
          </Box>
        )
      },
    },
  ]

  const embeddingModelColumns = [
    {
      field: 'id',
      headerName: 'ID',
      flex: 1,
      minWidth: 250,
    },
    {
      field: 'model_name',
      headerName: 'Name',
      flex: 1,
    },
    {
      field: 'address',
      headerName: 'Address',
      flex: 1,
    },
    {
      field: 'accelerators',
      headerName: 'GPU Indexes',
      flex: 1,
    },
    {
      field: 'url',
      headerName: 'Actions',
      flex: 1,
      minWidth: 200,
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
      renderCell: ({ row }) => {
        const url = row.url
        const closeUrl = `${endPoint}/v1/models/` + url

        if (url === 'IS_LOADING') {
          return <div></div>
        }

        return (
          <Box
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'left',
              alignItems: 'left',
            }}
          >
            <button
              title="Terminate Model"
              style={{
                borderWidth: '0px',
                backgroundColor: 'transparent',
                paddingLeft: '0px',
                paddingRight: '10px',
              }}
              onClick={() => {
                if (isCallingApi || isUpdatingModel) {
                  return
                }
                setIsCallingApi(true)
                fetch(closeUrl, {
                  method: 'DELETE',
                })
                  .then((response) => {
                    response.json()
                  })
                  .then(() => {
                    setIsCallingApi(false)
                  })
                  .catch((error) => {
                    console.error('Error:', error)
                    setIsCallingApi(false)
                  })
              }}
            >
              <Box
                width="40px"
                m="0 auto"
                p="5px"
                display="flex"
                justifyContent="center"
                borderRadius="4px"
                style={{
                  border: '1px solid #e5e7eb',
                  borderWidth: '1px',
                  borderColor: '#e5e7eb',
                }}
              >
                <DeleteOutlineOutlinedIcon />
              </Box>
            </button>
          </Box>
        )
      },
    },
  ]

  const imageModelColumns = embeddingModelColumns
  const rerankModelColumns = embeddingModelColumns

  return (
    <Box m="20px">
      <Title title="Running Models" />
      <TabContext value={tabValue}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <TabList
            value={tabValue}
            onChange={handleTabChange}
            aria-label="tabs"
          >
            <Tab label="Language Models" value="1" />
            <Tab label="Embedding Models" value="2" />
            <Tab label="Image models" value="3" />
            <Tab label="Rerank models" value="4" />
          </TabList>
        </Box>
        <TabPanel value="1" sx={{ padding: 0 }}>
          <Box m="40px 0 0 0" height="30vh">
            <DataGrid
              rows={llmData}
              columns={llmColumns}
              sx={{
                '& .MuiDataGrid-main': {
                  width: '95% !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-row': {
                  background: 'white',
                  margin: '10px 0px',
                },
                '& .MuiDataGrid-cell': {
                  borderBottom: 'none',
                },
                '& .CustomWide-cell': {
                  minWidth: '250px !important',
                },
                '& .MuiDataGrid-columnHeaders': {
                  borderBottom: 'none',
                },
                '& .MuiDataGrid-columnHeaderTitle': {
                  fontWeight: 'bold',
                },
                '& .MuiDataGrid-virtualScroller': {
                  overflowX: 'visible !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-footerContainer': {
                  borderTop: 'none',
                },
                'border-width': '0px',
              }}
              slots={{
                noRowsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models
                  </Stack>
                ),
                noResultsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models Matches
                  </Stack>
                ),
              }}
            />
          </Box>
        </TabPanel>
        <TabPanel value="2" sx={{ padding: 0 }}>
          <Box m="40px 0 0 0" height="30vh">
            <DataGrid
              rows={embeddingModelData}
              columns={embeddingModelColumns}
              sx={{
                '& .MuiDataGrid-main': {
                  width: '95% !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-row': {
                  background: 'white',
                  margin: '10px 0px',
                },
                '& .MuiDataGrid-cell': {
                  borderBottom: 'none',
                },
                '& .CustomWide-cell': {
                  minWidth: '250px !important',
                },
                '& .MuiDataGrid-columnHeaders': {
                  borderBottom: 'none',
                },
                '& .MuiDataGrid-columnHeaderTitle': {
                  fontWeight: 'bold',
                },
                '& .MuiDataGrid-virtualScroller': {
                  overflowX: 'visible !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-footerContainer': {
                  borderTop: 'none',
                },
                'border-width': '0px',
              }}
              slots={{
                noRowsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models
                  </Stack>
                ),
                noResultsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models Matches
                  </Stack>
                ),
              }}
            />
          </Box>
        </TabPanel>
        <TabPanel value="3" sx={{ padding: 0 }}>
          <Box m="40px 0 0 0" height="30vh">
            <DataGrid
              rows={imageModelData}
              columns={imageModelColumns}
              sx={{
                '& .MuiDataGrid-main': {
                  width: '95% !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-row': {
                  background: 'white',
                  margin: '10px 0px',
                },
                '& .MuiDataGrid-cell': {
                  borderBottom: 'none',
                },
                '& .CustomWide-cell': {
                  minWidth: '250px !important',
                },
                '& .MuiDataGrid-columnHeaders': {
                  borderBottom: 'none',
                },
                '& .MuiDataGrid-columnHeaderTitle': {
                  fontWeight: 'bold',
                },
                '& .MuiDataGrid-virtualScroller': {
                  overflowX: 'visible !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-footerContainer': {
                  borderTop: 'none',
                },
                'border-width': '0px',
              }}
              slots={{
                noRowsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models
                  </Stack>
                ),
                noResultsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models Matches
                  </Stack>
                ),
              }}
            />
          </Box>
        </TabPanel>
        <TabPanel value="4" sx={{ padding: 0 }}>
          <Box m="40px 0 0 0" height="30vh">
            <DataGrid
              rows={rerankModelData}
              columns={rerankModelColumns}
              sx={{
                '& .MuiDataGrid-main': {
                  width: '95% !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-row': {
                  background: 'white',
                  margin: '10px 0px',
                },
                '& .MuiDataGrid-cell': {
                  borderBottom: 'none',
                },
                '& .CustomWide-cell': {
                  minWidth: '250px !important',
                },
                '& .MuiDataGrid-columnHeaders': {
                  borderBottom: 'none',
                },
                '& .MuiDataGrid-columnHeaderTitle': {
                  fontWeight: 'bold',
                },
                '& .MuiDataGrid-virtualScroller': {
                  overflowX: 'visible !important',
                  overflow: 'visible',
                },
                '& .MuiDataGrid-footerContainer': {
                  borderTop: 'none',
                },
                'border-width': '0px',
              }}
              slots={{
                noRowsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models
                  </Stack>
                ),
                noResultsOverlay: () => (
                  <Stack
                    height="100%"
                    alignItems="center"
                    justifyContent="center"
                  >
                    No Running Models Matches
                  </Stack>
                ),
              }}
            />
          </Box>
        </TabPanel>
      </TabContext>
    </Box>
  )
}

export default RunningModels
