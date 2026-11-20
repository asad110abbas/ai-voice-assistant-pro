import client from './client'

export const exportCallsCsv = async () => {
  const res = await client.get('/export/calls.csv', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'calls.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export const exportTicketsCsv = async () => {
  const res = await client.get('/export/tickets.csv', { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'tickets.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export const exportTicketPdf = async (ticketId: number) => {
  const res = await client.get(`/export/tickets/${ticketId}.pdf`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `ticket_${ticketId}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
