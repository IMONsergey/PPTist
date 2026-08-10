import { useSlidesStore } from '@/store'
import type { PPTElement, PPTElementLink } from '@/types/slides'
import useHistorySnapshot from '@/hooks/useHistorySnapshot'
import message from '@/utils/message'

export default () => {
  const slidesStore = useSlidesStore()

  const { addHistorySnapshot } = useHistorySnapshot()

  const setLink = (handleElement: PPTElement, link: PPTElementLink) => {
    const linkRegExp = /^(https?):\/\/[\w\-]+(\.[\w\-]+)+([\w\-.,@?^=%&:\/~+#]*[\w\-@?^=%&\/~+#])?$/
    if (link.type === 'web' && !linkRegExp.test(link.target)) {
      message.error('Некорректный адрес веб-ссылки')
      return false
    }
    if (link.type === 'slide' && !link.target) {
      message.error('Сначала выберите цель ссылки')
      return false
    }
    const props = { link }
    slidesStore.updateElement({ id: handleElement.id, props })
    addHistorySnapshot()

    return true
  }

  const removeLink = (handleElement: PPTElement) => {
    slidesStore.removeElementProps({ id: handleElement.id, propName: 'link' })
    addHistorySnapshot()
  }

  return {
    setLink,
    removeLink,
  }
}