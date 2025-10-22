BlockingError("Blocking call to time.sleep\n\nHeads up! LangGraph dev identified a synchronous blocking call in your code. When running in an ASGI web server, blocking calls can degrade performance for everyone since they tie up the event loop.\n\nHere are your options to fix this:\n\n1. Best approach: Convert any blocking code to use async/await patterns\n   For example, use 'await aiohttp.get()' instead of 'requests.get()'\n\n2. Quick fix: Move blocking operations to a separate thread\n   Example: 'await asyncio.to_thread(your_blocking_function)'\n\n3. Override (if you can't change the code):\n   - For development: Run 'langgraph dev --allow-blocking'\n   - For deployment: Set 'BG_JOB_ISOLATED_LOOPS=true' environment variable\n\nThese blocking operations can prevent health checks and slow down other runs in your deployment. Following these recommendations will help keep your LangGraph application running smoothly!")Traceback (most recent call last):


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_base_client.py", line 1047, in request
    response = self._client.send(
               ^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpx/_client.py", line 914, in send
    response = self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpx/_client.py", line 942, in _send_handling_auth
    response = self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpx/_client.py", line 979, in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpx/_client.py", line 1014, in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpx/_transports/default.py", line 250, in handle_request
    resp = self._pool.handle_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpcore/_sync/connection_pool.py", line 256, in handle_request
    raise exc from None


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpcore/_sync/connection_pool.py", line 236, in handle_request
    response = connection.handle_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpcore/_sync/connection.py", line 101, in handle_request
    raise exc


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpcore/_sync/connection.py", line 78, in handle_request
    stream = self._connect(request)
             ^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpcore/_sync/connection.py", line 124, in _connect
    stream = self._network_backend.connect_tcp(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/httpcore/_backends/sync.py", line 208, in connect_tcp
    sock = socket.create_connection(
           ^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/socket.py", line 850, in create_connection
    sock.connect(sa)


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/blockbuster/blockbuster.py", line 109, in wrapper
    raise BlockingError(func_name)


blockbuster.blockbuster.BlockingError: Blocking call to socket.socket.connect

Heads up! LangGraph dev identified a synchronous blocking call in your code. When running in an ASGI web server, blocking calls can degrade performance for everyone since they tie up the event loop.

Here are your options to fix this:

1. Best approach: Convert any blocking code to use async/await patterns
   For example, use 'await aiohttp.get()' instead of 'requests.get()'

2. Quick fix: Move blocking operations to a separate thread
   Example: 'await asyncio.to_thread(your_blocking_function)'

3. Override (if you can't change the code):
   - For development: Run 'langgraph dev --allow-blocking'
   - For deployment: Set 'BG_JOB_ISOLATED_LOOPS=true' environment variable

These blocking operations can prevent health checks and slow down other runs in your deployment. Following these recommendations will help keep your LangGraph application running smoothly!



During handling of the above exception, another exception occurred:



Traceback (most recent call last):


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 932, in generate
    self._generate_with_cache(


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 1178, in _generate_with_cache
    for chunk in self._stream(messages, stop=stop, **kwargs):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_anthropic/chat_models.py", line 1640, in _stream
    stream = self._create(payload)
             ^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_anthropic/chat_models.py", line 1619, in _create
    return self._client.messages.create(**payload)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_utils/_utils.py", line 282, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/resources/messages/messages.py", line 930, in create
    return self._post(
           ^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_base_client.py", line 1324, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_base_client.py", line 1070, in request
    self._sleep_for_retry(


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_base_client.py", line 1138, in _sleep_for_retry
    time.sleep(timeout)


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/blockbuster/blockbuster.py", line 109, in wrapper
    raise BlockingError(func_name)


blockbuster.blockbuster.BlockingError: Blocking call to time.sleep

Heads up! LangGraph dev identified a synchronous blocking call in your code. When running in an ASGI web server, blocking calls can degrade performance for everyone since they tie up the event loop.

Here are your options to fix this:

1. Best approach: Convert any blocking code to use async/await patterns
   For example, use 'await aiohttp.get()' instead of 'requests.get()'

2. Quick fix: Move blocking operations to a separate thread
   Example: 'await asyncio.to_thread(your_blocking_function)'

3. Override (if you can't change the code):
   - For development: Run 'langgraph dev --allow-blocking'
   - For deployment: Set 'BG_JOB_ISOLATED_LOOPS=true' environment variable

These blocking operations can prevent health checks and slow down other runs in your deployment. Following these recommendations will help keep your LangGraph application running smoothly!