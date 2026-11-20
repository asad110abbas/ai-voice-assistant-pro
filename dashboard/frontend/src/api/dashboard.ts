import client from './client'

export const getStats = () => client.get('/dashboard/stats')
export const getAnalytics = (type: string, days = 30) =>
  client.get('/dashboard/analytics', { params: { type, days } })
export const getCallOutcomes = (days = 30) =>
  client.get('/dashboard/call_outcomes', { params: { days } })
export const getCostStats = (days = 30) =>
  client.get('/dashboard/cost', { params: { days } })
