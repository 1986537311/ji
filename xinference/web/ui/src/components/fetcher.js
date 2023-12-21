import { Cookies } from 'react-cookie'

const cookies = new Cookies()

const updateOptions = (url, options) => {
  const update = { ...options }
  if (cookies.get('token') !== 'no_auth') {
    update.headers = {
      ...update.headers,
      Authorization: 'Bearer ' + cookies.get('token'),
    }
  }
  return update
}

export default function fetcher(url, options) {
  return fetch(url, updateOptions(url, options))
}
