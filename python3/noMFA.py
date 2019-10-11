import boto3
import smtplib

# Email realated

# here using Gmail as E-mail client
smtp_host = 'smtp.gmail.com'

smtp_user = '<sender_email_address>'
smtp_token = '<sender_email_password>'
subject = 'AWS Compliance Bot'
from_addr = '<sender_email_address>'


#Boto3 Related
iam = boto3.client('iam')
iam_users = []

Will ignore these users if you need
ignore_list = ['<exact username in AWS>']

#this email will be used if user's  email is not found
default_email = '<deafult@gmail.com>'

def  send_email(smtp_host, smtp_user, smtp_token, message, from_addr , to_addr):
    try:

        s = smtplib.SMTP(smtp_host, 587)
        s.starttls()
        s.login(smtp_user, smtp_token)
        s.sendmail(from_addr, to_addr ,message)
        s.quit()
        print("Email sent Successfully")
        return 'success'
    except Exception as e:
        print(e)
        print("Something wrong")
        return ''

def get_email(username,search_list, search_key):
    #This  filter will use entire list of dictonries and return with a list of dictonaries with exact filtered key
    filtered_list = list(filter(lambda tags: tags['Key'] == search_key, search_list))
    if len(filtered_list) != 0:
        for elem in filtered_list:
            email = elem['Value']

    else:
        #This condition if executed if there is atleast one tag and No E-mail Tag associated
        email = default_email
        create_tags(username , 'E-mail', email)

    return email


def get_tags_for_user(username):
    user_tags = iam.list_user_tags(UserName=username)
    print(user_tags)
    # This condition will be triggeredif no tag exists for IAM user and will create E-mail Tag with default_email
    if len(user_tags['Tags']) == 0:
        print(default_email)
        create_tags(username, 'E-mail', default_email)
    email = get_email(username, user_tags['Tags'], 'E-mail')
    return email

def create_tags(user, key, value):
    response = iam.tag_user(UserName=user, Tags=[{'Key': key, 'Value': value}, ])
    print("Tags Created for user ", user, "with key", key, "and value", value)

def getPassword(user):
    try:
        response = iam.get_login_profile(UserName=user)

        return response

    except iam.exceptions.NoSuchEntityException as e:
        print(e)
        return ''

response = iam.list_users()
for user in response['Users']:
    iam_users.append(user['UserName'])
while 'Marker' in response:
    response = iam.list_users(Marker=response['Marker'])
    for user in response['Users']:
        iam_users.append(user['UserName'])

no_mfa_users = []
for iam_user in iam_users:
    response = iam.list_mfa_devices(UserName=iam_user)
    if not response['MFADevices'] and iam_user not in ignore_list:
        no_mfa_users.append(iam_user)
        if getPassword(iam_user):
            text = 'Ensure your AWS account with username: ' + iam_user + ' is enabled with MFA. Console access has been disabled due to compliance requirements, please work with your devops team for further steps.'
            to_email = get_tags_for_user(iam_user)
            message = 'Subject: {}\n\n{}'.format(subject, text)
            send_email(smtp_host, smtp_user, smtp_token, message, from_addr , to_email)
            #response = iam.delete_login_profile(UserName=iam_user)



print(no_mfa_users)
