export const formatLocalTime = (utcTimestamp: string) => {
  // Create a date object from UTC timestamp
  const date = new Date(utcTimestamp + 'Z') // Append Z to treat as UTC
  
  // Format options for PDT time
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'America/Los_Angeles',
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric',
    hour12: true
  }

  return new Intl.DateTimeFormat('en-US', options).format(date)
} 