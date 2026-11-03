import type { Restaurant, MenuItem, AnalyticsData, ScrapeResult } from '../types';

export interface GetItemsParams {
  restaurantId?: number | null;
  search?: string;
  category?: string;
  cuisine?: string;
  minRating?: number;
  area?: string;
  minPrice?: number;
  maxPrice?: number;
  sort?: 'price_asc' | 'price_desc' | 'name_asc' | 'name_desc' | 'rating_desc' | 'newest';
  limit?: number;
  offset?: number;
}

export interface ScrapeOptions {
  url: string;
  name?: string;
  rating?: number;
  cuisine?: string;
  opening_hours?: string;
  address?: string;
  lat?: number;
  lon?: number;
  area?: string;
  render?: boolean;
}

export interface UpdateRestaurantParams {
  id: number;
  name?: string;
  rating?: number;
  cuisine?: string;
  opening_hours?: string;
  address?: string;
  lat?: number;
  lon?: number;
  area?: string;
}

export interface GetItemsResponse {
  success: boolean;
  total: number;
  count: number;
  limit: number;
  offset: number;
  items: MenuItem[];
}

let staticItemsCache: MenuItem[] | null = null;

async function tryFetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    const contentType = res.headers.get('content-type') || '';
    if (res.ok && contentType.includes('application/json')) {
      return (await res.json()) as T;
    }
  } catch {
    // Local dev server not running or deployed on static host (e.g. Vercel)
  }
  return null;
}

async function postJson<T>(url: string, body: unknown, fallbackErrorPrefix: string): Promise<T | null> {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const contentType = res.headers.get('content-type') || '';
    if (res.ok && contentType.includes('application/json')) {
      return (await res.json()) as T;
    }
    if (!res.ok && contentType.includes('application/json')) {
      const errData = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(errData.error || `${fallbackErrorPrefix} (HTTP ${res.status})`);
    }
  } catch (err: unknown) {
    if (err instanceof Error && err.message.includes(fallbackErrorPrefix)) {
      throw err;
    }
  }
  return null;
}

export const api = {
  async getRestaurants(): Promise<{ success: boolean; count: number; restaurants: Restaurant[] }> {
    const data = await tryFetchJson<{ success: boolean; count: number; restaurants: Restaurant[] }>('/api/restaurants');
    if (data?.success && Array.isArray(data.restaurants)) {
      return data;
    }

    const staticRes = await fetch('/data/restaurants.json');
    if (!staticRes.ok) throw new Error(`Failed to fetch restaurants: ${staticRes.statusText}`);
    return staticRes.json();
  },

  async getMenuItems(params: GetItemsParams = {}): Promise<GetItemsResponse> {
    const query = new URLSearchParams();
    if (params.restaurantId) query.set('restaurant_id', String(params.restaurantId));
    if (params.search) query.set('search', params.search);
    if (params.category) query.set('category', params.category);
    if (params.cuisine) query.set('cuisine', params.cuisine);
    if (params.minRating != null) query.set('min_rating', String(params.minRating));
    if (params.area) query.set('area', params.area);
    if (params.minPrice != null) query.set('min_price', String(params.minPrice));
    if (params.maxPrice != null) query.set('max_price', String(params.maxPrice));
    if (params.sort) query.set('sort', params.sort);
    if (params.limit != null) query.set('limit', String(params.limit));
    if (params.offset != null) query.set('offset', String(params.offset));

    const data = await tryFetchJson<GetItemsResponse>(`/api/items?${query.toString()}`);
    if (data?.success && Array.isArray(data.items)) {
      return data;
    }

    // Static fallback: load items.json and filter in-memory with identical semantics
    if (!staticItemsCache) {
      const staticRes = await fetch('/data/items.json');
      if (!staticRes.ok) throw new Error(`Failed to fetch menu items: ${staticRes.statusText}`);
      staticItemsCache = await staticRes.json();
    }

    let filtered = [...(staticItemsCache || [])];

    if (params.restaurantId) {
      filtered = filtered.filter((item) => item.restaurant_id === params.restaurantId);
    }
    if (params.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter((item) =>
        item.name.toLowerCase().includes(q) ||
        item.description?.toLowerCase().includes(q) ||
        item.restaurant_name?.toLowerCase().includes(q) ||
        item.cuisine?.toLowerCase().includes(q)
      );
    }
    if (params.category) {
      filtered = filtered.filter((item) => item.category === params.category);
    }
    if (params.cuisine) {
      const q = params.cuisine.toLowerCase();
      filtered = filtered.filter((item) => item.cuisine?.toLowerCase().includes(q));
    }
    if (params.minRating != null) {
      filtered = filtered.filter((item) => item.rating != null && item.rating >= params.minRating!);
    }
    if (params.area) {
      filtered = filtered.filter((item) => item.area === params.area);
    }
    if (params.minPrice != null) {
      filtered = filtered.filter((item) => item.price >= params.minPrice!);
    }
    if (params.maxPrice != null) {
      filtered = filtered.filter((item) => item.price <= params.maxPrice!);
    }

    const sort = params.sort || 'price_desc';
    if (sort === 'price_asc') filtered.sort((a, b) => a.price - b.price);
    else if (sort === 'price_desc') filtered.sort((a, b) => b.price - a.price);
    else if (sort === 'name_asc') filtered.sort((a, b) => a.name.localeCompare(b.name));
    else if (sort === 'name_desc') filtered.sort((a, b) => b.name.localeCompare(a.name));
    else if (sort === 'rating_desc') {
      filtered.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0) || b.price - a.price);
    } else if (sort === 'newest') {
      filtered.sort((a, b) => b.id - a.id);
    }

    const total = filtered.length;
    const limit = params.limit ?? 25;
    const offset = params.offset ?? 0;
    const items = filtered.slice(offset, offset + limit);

    return {
      success: true,
      total,
      count: items.length,
      limit,
      offset,
      items,
    };
  },

  async getAnalytics(): Promise<AnalyticsData> {
    const data = await tryFetchJson<AnalyticsData>('/api/analytics');
    if (data?.success && data.kpi) {
      return data;
    }

    const staticRes = await fetch('/data/analytics.json');
    if (!staticRes.ok) throw new Error(`Failed to fetch analytics: ${staticRes.statusText}`);
    return staticRes.json();
  },

  async scrapeUrl(options: ScrapeOptions): Promise<ScrapeResult> {
    const data = await postJson<ScrapeResult>('/api/scrape', options, 'Scrape failed');
    if (data) return data;

    // Static showcase fallback (e.g. on Vercel deployment):
    // Check if the requested target URL or name matches an already-scraped restaurant in the dataset
    try {
      const restData = await this.getRestaurants();
      const normalizeUrl = (u?: string | null) => (u || '').toLowerCase().split('?')[0].replace(/\/+$/, '');
      const targetClean = normalizeUrl(options.url);

      const match = restData.restaurants.find((r) => {
        if (r.grab_url && normalizeUrl(r.grab_url) === targetClean) return true;
        if (r.foodpanda_url && normalizeUrl(r.foodpanda_url) === targetClean) return true;
        if (r.website && normalizeUrl(r.website) === targetClean) return true;
        if (options.name && r.name.toLowerCase().includes(options.name.toLowerCase())) return true;
        return false;
      });

      if (match && match.item_count > 0) {
        const itemsRes = await this.getMenuItems({ restaurantId: match.id, limit: 1000 });
        return {
          success: true,
          restaurantId: match.id,
          isMerged: true,
          restaurantName: match.name,
          rating: match.rating ?? undefined,
          cuisine: match.cuisine ?? undefined,
          openingHours: match.opening_hours ?? undefined,
          address: match.address ?? undefined,
          lat: match.lat ?? undefined,
          lon: match.lon ?? undefined,
          area: match.area ?? undefined,
          source: match.grab_url ? 'grabfood' : match.foodpanda_url ? 'foodpanda' : 'website',
          url: options.url,
          itemsCount: itemsRes.total,
          items: itemsRes.items.map((i) => ({
            name: i.name,
            price: i.price,
            description: i.description || '',
            category: i.category || 'Menu',
            currency: i.currency || 'MYR',
          })),
          elapsedMs: 720,
        };
      }
    } catch {
      // ignore and fall through to descriptive error
    }

    throw new Error(
      'Live scraping of unindexed URLs requires the local development environment (Node.js & Python Playwright). To run headless Chromium scraping on new URLs, run "npm run dev" locally. On this live Vercel showcase, select a preset (e.g. Pizza Hut or Subway) to preview the complete scraping pipeline.'
    );
  },

  async updateRestaurant(params: UpdateRestaurantParams): Promise<{ success: boolean; message: string }> {
    const data = await postJson<{ success: boolean; message: string }>(
      '/api/update-restaurant',
      params,
      'Failed to update restaurant parameters'
    );
    if (data) return data;

    return {
      success: true,
      message: 'Demo update applied locally. Permanent database writes require the local development server.',
    };
  },

  async addLink(
    name: string,
    url: string,
    extra: Partial<UpdateRestaurantParams> = {}
  ): Promise<{ success: boolean; isMerged?: boolean; message: string }> {
    const data = await postJson<{ success: boolean; isMerged?: boolean; message: string }>(
      '/api/add-link',
      { name, url, ...extra },
      'Failed to add link'
    );
    if (data) return data;

    return {
      success: true,
      message: 'Demo link added. Permanent database ingestion requires running the local development scraper.',
    };
  },

  getExportUrl(format: 'csv' | 'json' = 'csv'): string {
    if (
      typeof window !== 'undefined' &&
      (window.location.hostname.includes('vercel.app') || window.location.hostname.includes('netlify.app'))
    ) {
      return format === 'json' ? '/data/restaurant_menu_dataset.json' : '/data/menu_items.csv';
    }
    return `/api/export?format=${format}`;
  },
};

