BadRequestError("Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'prompt is too long: 201579 tokens > 200000 maximum'}, 'request_id': 'req_011CUNNgHw3Wr6tRT3AaPiiC'}")Traceback (most recent call last):


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 1296, in _agenerate_with_cache
    async for chunk in self._astream(messages, stop=stop, **kwargs):


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_anthropic/chat_models.py", line 1696, in _astream
    _handle_anthropic_bad_request(e)


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_anthropic/chat_models.py", line 1676, in _astream
    stream = await self._acreate(payload)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/langchain_anthropic/chat_models.py", line 1624, in _acreate
    return await self._async_client.messages.create(**payload)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/resources/messages/messages.py", line 2113, in create
    return await self._post(
           ^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_base_client.py", line 1898, in post
    return await self.request(cast_to, opts, stream=stream, stream_cls=stream_cls)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


  File "/opt/miniconda3/envs/deepagents-test/lib/python3.12/site-packages/anthropic/_base_client.py", line 1698, in request
    raise self._make_status_error_from_response(err.response) from None


anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'prompt is too long: 201579 tokens > 200000 maximum'}, 'request_id': 'req_011CUNNgHw3Wr6tRT3AaPiiC'}