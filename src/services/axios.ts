import axios from 'axios'
import message from '@/utils/message'

const instance = axios.create({ timeout: 1000 * 300 })

instance.interceptors.response.use(
  response => {
    if (response.status >= 200 && response.status < 400) {
      return Promise.resolve(response.data)
    }

    message.error('Неизвестная ошибка запроса.')
    return Promise.reject(response)
  },
  error => {
    if (error && error.response) {
      if (error.response.status >= 400 && error.response.status < 500) {
        return Promise.reject(error.message)
      }
      else if (error.response.status >= 500) {
        return Promise.reject(error.message)
      }

      message.error('Сервер столкнулся с неизвестной ошибкой.')
      return Promise.reject(error.message)
    }

    message.error('Не удалось подключиться или истекло время ожидания запроса.')
    return Promise.reject(error)
  }
)

export default instance