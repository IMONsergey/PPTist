// Russian locale for Apache ECharts.
// Terminology follows the Russian locale shipped by Apache ECharts.

export const ECHARTS_RU_LOCALE = {
  time: {
    month: [
      'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
    ],
    monthAbbr: [
      'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
      'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек',
    ],
    dayOfWeek: [
      'Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота',
    ],
    dayOfWeekAbbr: ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'],
  },
  legend: {
    selector: {
      all: 'Всё',
      inverse: 'Обратить',
    },
  },
  toolbox: {
    brush: {
      title: {
        rect: 'Выделить область',
        polygon: 'Инструмент «Лассо»',
        lineX: 'Горизонтальное выделение',
        lineY: 'Вертикальное выделение',
        keep: 'Оставить выбранное',
        clear: 'Очистить выбранное',
      },
    },
    dataView: {
      title: 'Данные',
      lang: ['Данные', 'Закрыть', 'Обновить'],
    },
    dataZoom: {
      title: {
        zoom: 'Увеличить',
        back: 'Сбросить увеличение',
      },
    },
    magicType: {
      title: {
        line: 'Переключиться на линейный график',
        bar: 'Переключиться на столбчатую диаграмму',
        stack: 'Стопка',
        tiled: 'Плитка',
      },
    },
    restore: {
      title: 'Восстановить',
    },
    saveAsImage: {
      title: 'Сохранить изображение',
      lang: ['Щёлкните правой кнопкой мыши, чтобы сохранить изображение'],
    },
  },
  series: {
    typeNames: {
      pie: 'Круговая диаграмма',
      bar: 'Столбчатая диаграмма',
      line: 'Линейный график',
      scatter: 'Точечная диаграмма',
      effectScatter: 'Точечная диаграмма с эффектами',
      radar: 'Лепестковая диаграмма',
      tree: 'Дерево',
      treemap: 'Древовидная карта',
      boxplot: 'Ящик с усами',
      candlestick: 'Свечной график',
      k: 'Свечной график',
      heatmap: 'Тепловая карта',
      map: 'Карта',
      parallel: 'Диаграмма параллельных координат',
      lines: 'Линейный граф',
      graph: 'Граф связей',
      sankey: 'Диаграмма Санкей',
      funnel: 'Воронка',
      gauge: 'Шкала',
      pictorialBar: 'Пиктографическая столбчатая диаграмма',
      themeRiver: 'Тематическая река',
      sunburst: 'Солнечная диаграмма',
      custom: 'Пользовательская диаграмма',
      chart: 'диаграмма',
    },
  },
  aria: {
    general: {
      withTitle: 'Это диаграмма «{title}»',
      withoutTitle: 'Это диаграмма',
    },
    series: {
      single: {
        prefix: '',
        withName: ' типа {seriesType} с названием {seriesName}.',
        withoutName: ' типа {seriesType}.',
      },
      multiple: {
        prefix: '. Она состоит из {seriesCount} рядов.',
        withName: ' Ряд {seriesId} имеет тип {seriesType} и показывает {seriesName}.',
        withoutName: ' Ряд {seriesId} имеет тип {seriesType}.',
        separator: {
          middle: '',
          end: '',
        },
      },
    },
    data: {
      allData: 'Данные: ',
      partialData: 'Первые {displayCnt} элементов: ',
      withName: 'значение для {name} — {value}',
      withoutName: '{value}',
      separator: {
        middle: ', ',
        end: '. ',
      },
    },
  },
}
