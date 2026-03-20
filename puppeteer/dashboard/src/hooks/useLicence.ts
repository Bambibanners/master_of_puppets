import { useQuery } from '@tanstack/react-query';
import { authenticatedFetch } from '../auth';

export interface LicenceInfo {
  edition: 'community' | 'enterprise';
  customer_id?: string;
  expires?: string;     // ISO 8601 datetime string
  features?: string[];  // enabled EE feature names
}

const CE_DEFAULTS: LicenceInfo = {
  edition: 'community',
};

export function useLicence(): LicenceInfo {
  const { data } = useQuery<LicenceInfo>({
    queryKey: ['licence'],
    queryFn: async () => {
      const res = await authenticatedFetch('/api/licence');
      if (!res.ok) return CE_DEFAULTS;
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // cache 5 minutes
    retry: false,
  });
  return data ?? CE_DEFAULTS;
}
