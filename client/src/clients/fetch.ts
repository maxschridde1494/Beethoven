interface GenerateFetchClientProps {
  body?: BodyInit
  headers?: Headers
  method: string
  path: string
  baseUrl?: string
}

export const generateFetchRequest = ({
  body,
  headers = new Headers(),
  method,
  path,
  baseUrl = window.location.origin,
}: GenerateFetchClientProps): Request => {
  const requestArgs: RequestInit = {
    method,
    headers: new Headers({
      'Content-Type': 'application/json',
      ...headers,
    }),
    ...(body ? { body } : {}),
  };

  const url = new URL(path, baseUrl).toString();

  return new Request(url, requestArgs);
};

type SimpleFetchParamsType = { 
  errMsgResolver?: (data: any) => string;
  onError?: (err: Error) => void;
  onSuccess?: (data: any) => void;
  requestWasSuccessful?: (data: any) => boolean; 
  url: string;
}

export const simpleFetch = async ({ errMsgResolver, onError, onSuccess, requestWasSuccessful, url }: SimpleFetchParamsType) => {
  try {
    const response = await fetch(url)
    const data = await response.json()
  
    if (response.status != 200 || (requestWasSuccessful && !requestWasSuccessful(data))) {
      if (errMsgResolver) throw new Error(errMsgResolver(data))
      throw new Error(data.message)
    }

    if (onSuccess) onSuccess(data)
  } catch(e: any){
    console.error(e)
    if (onError) onError(e)
  }
}
