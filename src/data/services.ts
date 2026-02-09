export type Service = {
  category: string;
  title: string;
  slug: string;
  shortDescription: string;
  description: string;
  durationMin: number;
  priceFrom: number;
  image: string;
  tags: string[];
};

export const services: Service[] = [
  {
    category: "Расслабление",
    title: "Арома-релакс массаж",
    slug: "aroma-relax",
    shortDescription: "Мягкие техники с тёплыми маслами для полного перезапуска.",
    description:
      "Деликатная программа расслабления с акцентом на дыхание и плавные движения. Используем натуральные масла и мягкий свет, чтобы снять напряжение, восстановить сон и подарить ощущение спокойствия.",
    durationMin: 60,
    priceFrom: 3500,
    image: "/images/aroma-relax.jpg",
    tags: ["антистресс", "масла", "мягкий эффект"]
  },
  {
    category: "Тонус",
    title: "Скульптурирующий массаж",
    slug: "sculpt",
    shortDescription: "Тонизирующая техника для упругости и лёгкости тела.",
    description:
      "Акцент на лимфодренаж, моделирование силуэта и улучшение микроциркуляции. Подходит для тех, кто хочет почувствовать тело более упругим и лёгким уже после первой процедуры.",
    durationMin: 75,
    priceFrom: 4200,
    image: "/images/sculpt.jpg",
    tags: ["лимфодренаж", "тонус", "силуэт"]
  },
  {
    category: "Спа",
    title: "Шоколадный уход",
    slug: "chocolate-spa",
    shortDescription: "Питательное обёртывание и расслабляющий массаж.",
    description:
      "Ритуал с тёплым шоколадным составом, который глубоко питает кожу и дарит ощущение комфорта. Завершается нежным массажем и ароматерапией.",
    durationMin: 90,
    priceFrom: 5200,
    image: "/images/chocolate-spa.jpg",
    tags: ["spa", "питание", "ритуал"]
  },
  {
    category: "Восстановление",
    title: "Глубокий массаж спины",
    slug: "back-therapy",
    shortDescription: "Работа с зажимами и восстановление мобильности.",
    description:
      "Проработка мышц спины, шеи и плечевого пояса. Подходит тем, кто много работает за компьютером или испытывает напряжение в верхней части тела.",
    durationMin: 50,
    priceFrom: 3000,
    image: "/images/back-therapy.jpg",
    tags: ["спина", "осанка", "глубоко"]
  },
  {
    category: "Релакс",
    title: "Массаж для двоих",
    slug: "couple",
    shortDescription: "Синхронный сеанс в приватной атмосфере.",
    description:
      "Два мастера работают одновременно, создавая гармоничный ритм. Идеально для пары или подруг, чтобы разделить момент заботы и отдыха.",
    durationMin: 60,
    priceFrom: 6500,
    image: "/images/couple.jpg",
    tags: ["для двоих", "ритуал", "подарок"]
  },
  {
    category: "Тело",
    title: "Балийский массаж",
    slug: "bali",
    shortDescription: "Энергичная техника для глубокого расслабления.",
    description:
      "Сочетание растягивания, точечного давления и плавных движений. Помогает снять усталость, улучшить циркуляцию и восстановить энергию.",
    durationMin: 70,
    priceFrom: 4400,
    image: "/images/bali.jpg",
    tags: ["энергия", "баланс", "глубина"]
  },
  {
    category: "Лицо",
    title: "Лифтинг-массаж лица",
    slug: "face-lift",
    shortDescription: "Улучшение тонуса и сияния кожи без инъекций.",
    description:
      "Техника направлена на улучшение микроциркуляции, снятие отёчности и восстановление чёткости овала лица. Идеально перед важными событиями.",
    durationMin: 40,
    priceFrom: 2800,
    image: "/images/face-lift.jpg",
    tags: ["лицо", "сияние", "лифтинг"]
  },
  {
    category: "Восстановление",
    title: "Спортивный массаж",
    slug: "sport",
    shortDescription: "Снимает напряжение после тренировок и ускоряет восстановление.",
    description:
      "Интенсивная техника для тех, кто активно занимается спортом. Помогает уменьшить мышечную усталость, повысить гибкость и улучшить самочувствие.",
    durationMin: 60,
    priceFrom: 4000,
    image: "/images/sport.jpg",
    tags: ["спорт", "восстановление", "мышцы"]
  }
];
