import os
import boto3
import datetime
import zipfile
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def get_datetime():
    """現在時刻から日付文字列の取得

    Returns:
        str: 日付文字列（yyyymmdd形式）
    """
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)
    d = now.strftime('%Y%m%d')
    return d


def sendMail(s3_record):
    """メール送信処理

        参考(AWS公式)
        https://docs.aws.amazon.com/ses/latest/dg/
            send-an-email-using-sdk-programmatically.html#
                :~:text=Ruby-,Python,-This%20topic%20shows

    Args:
        s3_record (dict): S3ファイル情報
    """

    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = os.environ['SRC_MAIL']

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENT = os.environ['DST_MAIL']

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = 'ConfigSet'

    # If necessary, replace us-west-2 with the AWS Region you're using for
    # Amazon SES.
    AWS_REGION = 'ap-northeast-1'

    # Attach File Download from S3
    s3 = boto3.resource('s3')
    bucket = s3_record['bucket']['name']
    key = s3_record['object']['key']
    send_file = '/tmp/' + key[key.rfind('/') + 1:]
    s3.Bucket(bucket).download_file(key, send_file)

    # The email body for recipients with non-HTML email clients.
    if os.path.getsize(send_file) == 0:
        ATTACHMENT = ''
        BODY_TEXT = '本日の巡回結果は「なし」です。'
        # The subject line for the email.
        SUBJECT = '入札巡回結果通知メール（なし）'
    else:
        ATTACHMENT = '/tmp/crawling_report_' + get_datetime() + '.zip'
        # Attach File Zipped.
        with zipfile.ZipFile(ATTACHMENT, 'w', zipfile.ZIP_DEFLATED) as zip:
            zip.write(send_file)
        BODY_TEXT = '巡回結果、添付のリストが該当しましたのでお知らせします。'
        # The subject line for the email.
        SUBJECT = '入札巡回結果通知メール（該当あり）'

    # The HTML body of the email.
    BODY_HTML = BODY_TEXT

    # The character encoding for the email.
    CHARSET = 'utf-8'

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = RECIPIENT

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding.
    # This step is necessary if you're sending a message with
    # characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    if not ATTACHMENT == '':
        # Define the attachment part and encode it using MIMEApplication.
        att = MIMEApplication(open(ATTACHMENT, 'rb').read())

        # Add a header to tell the email client to treat this part
        # as an attachment, and to give the attachment a name.
        att.add_header('Content-Disposition', 'attachment',
                       filename=os.path.basename(ATTACHMENT))

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    if not ATTACHMENT == '':
        # Add the attachment to the parent container.
        msg.attach(att)

    # print(msg)
    try:
        # Provide the contents of the email.
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=[
                RECIPIENT
            ],
            RawMessage={
                'Data': msg.as_string(),
            },
            # ConfigurationSetName=CONFIGURATION_SET
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['ResponseMetadata']['RequestId'])


def lambda_handler(event, context):
    """lambda起動ハンドラ

    Args:
        event (any): 更新されたS3のファイル情報
        context (any): 未使用
    """

    # メール送信
    sendMail(event['Records'][0]['s3'])
