export type ServiceCategory = {
  id: number;
  title: string;
  slug: string;
  sort_order: number;
  is_active: boolean;
};

export type Service = {
  id: number;
  category_id: number;
  category?: ServiceCategory;
  title: string;
  slug: string;
  short_description: string;
  description: string;
  duration_min: number;
  price_from: number;
  price_to?: number | null;
  image_url?: string | null;
  tags: string[];
  is_active: boolean;
  sort_order: number;
  seo_title?: string | null;
  seo_description?: string | null;
};

export type AvailabilitySlot = {
  starts_at: string;
  ends_at: string;
};

export type Booking = {
  id: number;
  client_name: string;
  client_phone: string;
  service_id: number;
  starts_at: string;
  ends_at: string;
  comment?: string | null;
  status: string;
  source: string;
  is_read: boolean;
  created_at: string;
};

export type SettingsPayload = Record<string, unknown>;
