# !/usr/bin/env python

import argparse
import logging
from dingtalk_stream import AckMessage
import dingtalk_stream


def setup_logger():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def define_options():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--client_id', dest='client_id', required=True,
        help='app_key or suite_key from https://open-dev.digntalk.com'
    )
    parser.add_argument(
        '--client_secret', dest='client_secret', required=True,
        help='app_secret or suite_secret from https://open-dev.digntalk.com'
    )
    options = parser.parse_args()
    return options


class FileBotHandler(dingtalk_stream.ChatbotHandler):
    def __init__(self, logger: logging.Logger = None):
        super(dingtalk_stream.ChatbotHandler, self).__init__()
        if logger:
            self.logger = logger

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
        if incoming_message.message_type != 'file':
            return AckMessage.STATUS_OK, 'OK'

        download_codes = incoming_message.get_file_list()
        if not download_codes:
            return AckMessage.STATUS_OK, 'OK'

        file_name = None
        if incoming_message.file_content is not None:
            file_name = incoming_message.file_content.file_name

        download_urls = []
        for download_code in download_codes:
            download_url = self.get_file_download_url(download_code)
            if download_url:
                self.logger.info('file download url: %s', download_url)
                download_urls.append(download_url)

        if download_urls:
            if len(download_urls) == 1:
                if file_name:
                    response = 'File: %s\nDownload URL: %s' % (file_name, download_urls[0])
                else:
                    response = 'Download URL: %s' % download_urls[0]
            else:
                lines = ['Download URLs:']
                lines.extend(['%d. %s' % (idx + 1, url) for idx, url in enumerate(download_urls)])
                response = '\n'.join(lines)
            self.reply_text(response, incoming_message)

        return AckMessage.STATUS_OK, 'OK'


def main():
    logger = setup_logger()
    options = define_options()

    credential = dingtalk_stream.Credential(options.client_id, options.client_secret)
    client = dingtalk_stream.DingTalkStreamClient(credential)
    client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC, FileBotHandler(logger))
    client.start_forever()


if __name__ == '__main__':
    main()
