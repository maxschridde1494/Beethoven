// HTTP Method types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

// API Response types
export interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  error?: string;
  status?: number;
}

// Error response type
export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

// Fetch client configuration
interface GenerateFetchClientProps {
  body?: BodyInit;
  headers?: HeadersInit;
  method: HttpMethod;
  path: string;
  baseUrl?: string;
}

export const generateFetchRequest = ({
  body,
  headers = {},
  method,
  path,
  baseUrl = window.location.origin,
}: GenerateFetchClientProps): Request => {
  const requestHeaders = new Headers({
    'Content-Type': 'application/json',
    ...headers,
  });

  const requestArgs: RequestInit = {
    method,
    headers: requestHeaders,
    ...(body ? { body } : {}),
  };

  const url = new URL(path, baseUrl).toString();

  return new Request(url, requestArgs);
};

// Simple fetch parameters with generics
interface SimpleFetchParams<TData = unknown, TError = ApiError> {
  url: string;
  errMsgResolver?: (data: TError) => string;
  onError?: (err: Error) => void;
  onSuccess?: (data: TData) => void;
  requestWasSuccessful?: (data: TData) => boolean;
}

// Simple fetch result type
interface SimpleFetchResult<TData = unknown> {
  data?: TData;
  success: boolean;
  error?: Error;
}

export const simpleFetch = async <TData = unknown, TError = ApiError>({
  url,
  errMsgResolver,
  onError,
  onSuccess,
  requestWasSuccessful,
}: SimpleFetchParams<TData, TError>): Promise<SimpleFetchResult<TData>> => {
  try {
    const response = await fetch(url);
    
    // Check if response is ok first
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Unknown error' })) as TError;
      const errorMessage = errMsgResolver ? errMsgResolver(errorData) : 'Request failed';
      throw new Error(errorMessage);
    }

    const data = await response.json() as TData;

    // Check custom success condition
    if (requestWasSuccessful && !requestWasSuccessful(data)) {
      const errorMessage = errMsgResolver ? errMsgResolver(data as unknown as TError) : 'Request was not successful';
      throw new Error(errorMessage);
    }

    // Call success callback if provided
    if (onSuccess) {
      onSuccess(data);
    }

    return { data, success: true };
  } catch (error: unknown) {
    const err = error instanceof Error ? error : new Error('Unknown error occurred');
    console.error('Fetch error:', err);
    
    // Call error callback if provided
    if (onError) {
      onError(err);
    }

    return { success: false, error: err };
  }
};

// Advanced fetch with full configuration
interface AdvancedFetchParams<TData = unknown, TError = ApiError> extends Omit<SimpleFetchParams<TData, TError>, 'url'> {
  method?: HttpMethod;
  path: string;
  baseUrl?: string;
  body?: BodyInit;
  headers?: HeadersInit;
  timeout?: number;
}

export const advancedFetch = async <TData = unknown, TError = ApiError>({
  method = 'GET',
  path,
  baseUrl = window.location.origin,
  body,
  headers = {},
  timeout = 10000,
  ...simpleFetchParams
}: AdvancedFetchParams<TData, TError>): Promise<SimpleFetchResult<TData>> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const request = generateFetchRequest({
      method,
      path,
      baseUrl,
      body,
      headers,
    });

    const response = await fetch(request, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Unknown error' })) as TError;
      const errorMessage = simpleFetchParams.errMsgResolver 
        ? simpleFetchParams.errMsgResolver(errorData) 
        : `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(errorMessage);
    }

    const data = await response.json() as TData;

    // Check custom success condition
    if (simpleFetchParams.requestWasSuccessful && !simpleFetchParams.requestWasSuccessful(data)) {
      const errorMessage = simpleFetchParams.errMsgResolver 
        ? simpleFetchParams.errMsgResolver(data as unknown as TError) 
        : 'Request was not successful';
      throw new Error(errorMessage);
    }

    // Call success callback if provided
    if (simpleFetchParams.onSuccess) {
      simpleFetchParams.onSuccess(data);
    }

    return { data, success: true };
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    
    const err = error instanceof Error ? error : new Error('Unknown error occurred');
    console.error('Advanced fetch error:', err);
    
    // Call error callback if provided
    if (simpleFetchParams.onError) {
      simpleFetchParams.onError(err);
    }

    return { success: false, error: err };
  }
};

// Utility type for JSON responses
export type JsonResponse<T> = Promise<SimpleFetchResult<T>>;

// Common HTTP status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
} as const;

export type HttpStatusCode = typeof HTTP_STATUS[keyof typeof HTTP_STATUS];
