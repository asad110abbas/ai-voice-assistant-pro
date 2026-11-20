import client from './client'

export const getTickets = (params?: Record<string, unknown>) =>
  client.get('/tickets', { params })

export const updateTicket = (id: number, data: Record<string, unknown>) =>
  client.patch(`/tickets/${id}`, data)

export const assignTicket = (id: number, agentId: number) =>
  client.post(`/tickets/${id}/assign?agent_id=${agentId}`)

export const getNotes = (ticketId: number) =>
  client.get(`/tickets/${ticketId}/notes`)

export const addNote = (ticketId: number, content: string) =>
  client.post(`/tickets/${ticketId}/notes`, { content })
