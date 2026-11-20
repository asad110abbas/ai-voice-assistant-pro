import client from './client'

export const getCalls = (params?: Record<string, unknown>) =>
  client.get('/calls', { params })

export const getCall = (id: number) => client.get(`/calls/${id}`)

export const getCallAudioUrl = (id: number) =>
  `http://localhost:8000/calls/${id}/audio`
