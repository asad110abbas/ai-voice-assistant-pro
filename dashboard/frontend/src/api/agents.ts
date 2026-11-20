import client from './client'

export const getAgents = () => client.get('/agents')

export const createAgent = (data: Record<string, unknown>) =>
  client.post('/agents', data)

export const updateAgent = (id: number, data: Record<string, unknown>) =>
  client.patch(`/agents/${id}`, data)
