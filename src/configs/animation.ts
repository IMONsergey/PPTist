import type { TurningMode } from '@/types/slides'

export const ANIMATION_DEFAULT_DURATION = 1000
export const ANIMATION_DEFAULT_TRIGGER = 'click'
export const ANIMATION_CLASS_PREFIX = 'animate__'

export const ENTER_ANIMATIONS = [
  {
    type: 'bounce',
    name: 'Отскок',
    children: [
      { name: 'Появление с отскоком', value: 'bounceIn' },
      { name: 'Слева с отскоком', value: 'bounceInLeft' },
      { name: 'Справа с отскоком', value: 'bounceInRight' },
      { name: 'Снизу с отскоком', value: 'bounceInUp' },
      { name: 'Сверху с отскоком', value: 'bounceInDown' },
    ],
  },
  {
    type: 'fade',
    name: 'Плавное',
    children: [
      { name: 'Плавное появление', value: 'fadeIn' },
      { name: 'Появление сверху', value: 'fadeInDown' },
      { name: 'Появление сверху (дальнее)', value: 'fadeInDownBig' },
      { name: 'Появление слева', value: 'fadeInLeft' },
      { name: 'Появление слева (дальнее)', value: 'fadeInLeftBig' },
      { name: 'Появление справа', value: 'fadeInRight' },
      { name: 'Появление справа (дальнее)', value: 'fadeInRightBig' },
      { name: 'Появление снизу', value: 'fadeInUp' },
      { name: 'Появление снизу (дальнее)', value: 'fadeInUpBig' },
      { name: 'Появление сверху слева', value: 'fadeInTopLeft' },
      { name: 'Появление сверху справа', value: 'fadeInTopRight' },
      { name: 'Появление снизу слева', value: 'fadeInBottomLeft' },
      { name: 'Появление снизу справа', value: 'fadeInBottomRight' },
    ],
  },
  {
    type: 'rotate',
    name: 'Поворот',
    children: [
      { name: 'Появление с поворотом', value: 'rotateIn' },
      { name: 'Поворот снизу слева', value: 'rotateInDownLeft' },
      { name: 'Поворот снизу справа', value: 'rotateInDownRight' },
      { name: 'Поворот сверху слева', value: 'rotateInUpLeft' },
      { name: 'Поворот сверху справа', value: 'rotateInUpRight' },
    ],
  },
  {
    type: 'zoom',
    name: 'Масштабирование',
    children: [
      { name: 'Появление с увеличением', value: 'zoomIn' },
      { name: 'Увеличение сверху', value: 'zoomInDown' },
      { name: 'Увеличение слева', value: 'zoomInLeft' },
      { name: 'Увеличение справа', value: 'zoomInRight' },
      { name: 'Увеличение снизу', value: 'zoomInUp' },
    ],
  },
  {
    type: 'slide',
    name: 'Сдвиг',
    children: [
      { name: 'Сдвиг сверху', value: 'slideInDown' },
      { name: 'Сдвиг слева', value: 'slideInLeft' },
      { name: 'Сдвиг справа', value: 'slideInRight' },
      { name: 'Сдвиг снизу', value: 'slideInUp' },
    ],
  },
  {
    type: 'flip',
    name: 'Переворот',
    children: [
      { name: 'Появление с переворотом по X', value: 'flipInX' },
      { name: 'Появление с переворотом по Y', value: 'flipInY' },
    ],
  },
  {
    type: 'back',
    name: 'Появление с масштабированием',
    children: [
      { name: 'Масштабирование сверху', value: 'backInDown' },
      { name: 'Масштабирование слева', value: 'backInLeft' },
      { name: 'Масштабирование справа', value: 'backInRight' },
      { name: 'Масштабирование снизу', value: 'backInUp' },
    ],
  },
  {
    type: 'lightSpeed',
    name: 'Быстрое появление',
    children: [
      { name: 'Быстрое появление справа', value: 'lightSpeedInRight' },
      { name: 'Быстрое появление слева', value: 'lightSpeedInLeft' },
    ],
  },
]

export const EXIT_ANIMATIONS = [
  {
    type: 'bounce',
    name: 'Отскок',
    children: [
      { name: 'Исчезновение с отскоком', value: 'bounceOut' },
      { name: 'Влево с отскоком', value: 'bounceOutLeft' },
      { name: 'Вправо с отскоком', value: 'bounceOutRight' },
      { name: 'Вверх с отскоком', value: 'bounceOutUp' },
      { name: 'Вниз с отскоком', value: 'bounceOutDown' },
    ],
  },
  {
    type: 'fade',
    name: 'Плавное',
    children: [
      { name: 'Плавное исчезновение', value: 'fadeOut' },
      { name: 'Исчезновение вниз', value: 'fadeOutDown' },
      { name: 'Исчезновение вниз (дальнее)', value: 'fadeOutDownBig' },
      { name: 'Исчезновение влево', value: 'fadeOutLeft' },
      { name: 'Исчезновение влево (дальнее)', value: 'fadeOutLeftBig' },
      { name: 'Исчезновение вправо', value: 'fadeOutRight' },
      { name: 'Исчезновение вправо (дальнее)', value: 'fadeOutRightBig' },
      { name: 'Исчезновение вверх', value: 'fadeOutUp' },
      { name: 'Исчезновение вверх (дальнее)', value: 'fadeOutUpBig' },
      { name: 'Исчезновение сверху слева', value: 'fadeOutTopLeft' },
      { name: 'Исчезновение сверху справа', value: 'fadeOutTopRight' },
      { name: 'Исчезновение снизу слева', value: 'fadeOutBottomLeft' },
      { name: 'Исчезновение снизу справа', value: 'fadeOutBottomRight' },
    ],
  },
  {
    type: 'rotate',
    name: 'Поворот',
    children: [
      { name: 'Исчезновение с поворотом', value: 'rotateOut' },
      { name: 'Выход с поворотом снизу слева', value: 'rotateOutDownLeft' },
      { name: 'Выход с поворотом снизу справа', value: 'rotateOutDownRight' },
      { name: 'Выход с поворотом сверху слева', value: 'rotateOutUpLeft' },
      { name: 'Выход с поворотом сверху справа', value: 'rotateOutUpRight' },
    ],
  },
  {
    type: 'zoom',
    name: 'Масштабирование',
    children: [
      { name: 'Исчезновение с уменьшением', value: 'zoomOut' },
      { name: 'Уменьшение вниз', value: 'zoomOutDown' },
      { name: 'Уменьшение влево', value: 'zoomOutLeft' },
      { name: 'Уменьшение вправо', value: 'zoomOutRight' },
      { name: 'Уменьшение вверх', value: 'zoomOutUp' },
    ],
  },
  {
    type: 'slide',
    name: 'Выезд',
    children: [
      { name: 'Выезд вниз', value: 'slideOutDown' },
      { name: 'Выезд влево', value: 'slideOutLeft' },
      { name: 'Выезд вправо', value: 'slideOutRight' },
      { name: 'Выезд вверх', value: 'slideOutUp' },
    ],
  },
  {
    type: 'flip',
    name: 'Переворот',
    children: [
      { name: 'Исчезновение с переворотом по X', value: 'flipOutX' },
      { name: 'Исчезновение с переворотом по Y', value: 'flipOutY' },
    ],
  },
  {
    type: 'back',
    name: 'Исчезновение с масштабированием',
    children: [
      { name: 'Масштабирование вниз', value: 'backOutDown' },
      { name: 'Масштабирование влево', value: 'backOutLeft' },
      { name: 'Масштабирование вправо', value: 'backOutRight' },
      { name: 'Масштабирование вверх', value: 'backOutUp' },
    ],
  },
  {
    type: 'lightSpeed',
    name: 'Быстрое исчезновение',
    children: [
      { name: 'Быстрое исчезновение вправо', value: 'lightSpeedOutRight' },
      { name: 'Быстрое исчезновение влево', value: 'lightSpeedOutLeft' },
    ],
  },
]

export const ATTENTION_ANIMATIONS = [
  {
    type: 'shake',
    name: 'Колебания',
    children: [
      { name: 'Горизонтальная тряска', value: 'shakeX' },
      { name: 'Вертикальная тряска', value: 'shakeY' },
      { name: 'Покачивание головой', value: 'headShake' },
      { name: 'Качание', value: 'swing' },
      { name: 'Колебания', value: 'wobble' },
      { name: 'Та-дам', value: 'tada' },
      { name: 'Желе', value: 'jello' },
    ],
  },
  {
    type: 'other',
    name: 'Другие',
    children: [
      { name: 'Отскок', value: 'bounce' },
      { name: 'Мигание', value: 'flash' },
      { name: 'Пульсация', value: 'pulse' },
      { name: 'Резинка', value: 'rubberBand' },
      { name: 'Сердцебиение', value: 'heartBeat' },
    ],
  },
]

interface SlideAnimation {
  label: string
  value: TurningMode
}

export const SLIDE_ANIMATIONS: SlideAnimation[] = [
  { label: 'Нет', value: 'no' },
  { label: 'Случайно', value: 'random' },
  { label: 'Сдвиг (влево/вправо)', value: 'slideX' },
  { label: 'Сдвиг (вверх/вниз)', value: 'slideY' },
  { label: '3D-сдвиг влево-вправо', value: 'slideX3D' },
  { label: '3D-сдвиг вверх-вниз', value: 'slideY3D' },
  { label: 'Затухание', value: 'fade' },
  { label: 'Поворот', value: 'rotate' },
  { label: 'Расширение вверх-вниз', value: 'scaleY' },
  { label: 'Расширение влево-вправо', value: 'scaleX' },
  { label: 'Увеличение', value: 'scale' },
  { label: 'Уменьшение', value: 'scaleReverse' },
]