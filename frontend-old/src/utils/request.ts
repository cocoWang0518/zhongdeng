import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.DEV ? '/api' : '/',
})

export default request
