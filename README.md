# A personal restaurant recommender


## DEV

`docker compose -f docker-compose-dev.yaml up --build`

## CI/CD

Run the self-hosted runner 'docker-builder' on WSL: `cd actions-runner` `./run.cmd`

If the SSH / SCP connection fails due to cert file being too open, it means that there is a conflict with WSL file management.
The runner runs on WSL, but due to being in a mount folder for easier visibility, chmod command cannot change 
file permissions since they are managed by Windows file system.

In WSL, go to `/etc/wsl.conf` and add:

```
[automount]
options = "metadata,umask=22,fmask=11"
```


## AWS

#### Configured services
- EC2 instance
- CloudWatch log stream
- email alert for "exited" in docker logger
- ~~S3 bucket~~
- IAM mfa
- PostgreSQL RDS

#### Access commands

First `cd aws/cert`

`ssh -i "ec2-docker-server-key.pem" ec2@RETRACTED-1.compute.amazonaws.com`

`scp -i "ec2-docker-server-key.pem" C:\Users\... ec2@RETRACTED.compute.amazonaws.com:/home/ec2...` `optional: -r for folders`

#### Updating EC2 codebase

**EC2**: /home/.., use `git pull origin` to update and prod compose to run. 

When making changes to .env, `scp -i "ec2-docker-server-key.pem" C:\Users\..\.env ec2@RETRACTED.compute.amazonaws.com:/home/.../.env`

Run:

`docker-compose -f docker-compose-prod.yaml up -d --build`

#### RDS

Using the same credentials as before. SSH into EC2 and use 

`psql -h database-RETRACTED.amazonaws.com -U ... -d postgres -p 5432`

Run `CREATE EXTENSION IF NOT EXISTS vector;` in psql if for some reason need to install pgvector

#### Configuring EC2

Install docker by the means necessary

For new EC2 instances

`sudo amazon-linux-extras enable postgresql14`

`sudo amazon-linux-extras install postgresql14`

Install JQ: `sudo yum install jq`

See cron instructions below

- `git clone https://github.com/jkuhno/wtf2eat.git`
- SCP copy .env file into the root project directory and fill the blanks
- SCP copy `/react-app/cert` with -r tag
- docker-compose run


#### ENV

Pay attention to line endings when handling ip-lookup script and cronjobs

##### .env

```

GROQ_API_KEY=<groq-api-key>

GOOGLE_API_KEY=<gemini-api-key>

GMAPS_API_KEY=<google-maps-api-key> //not needed now because accounts have their own but soon will again

POSTGRES_PASSWORD=<create-a-password> //used for both vector and user databases
POSTGRES_USER=<create-a-username> //same here
POSTGRES_DB=<database-name> // default 'postgres' works fine
POSTGRES_HOST_DEV='db'
POSTGRES_HOST_PROD='database-@RETRACTED.rds.amazonaws.com'

// these are used for dynamic IP updates with cron
CF_API_KEY=<cloudflare-api-key>
CF_ZONE_ID=<zone-id>
CF_DNS_RECORD_ID=<dns-record-id> // query from the cloudflare API, google instructions

// these are used for 'captcha' cheking, PROD  versions from cloudflare Turnstile, DEV from public docs
CF_TURNSTILE_SITE_PROD=<get-from-your-dashboard>
CF_TURNSTILE_SECRET_PROD=<get-from-your-dashboard>
CF_TURNSTILE_SITE_DEV='1x00000000000000000000AA'
CF_TURNSTILE_SECRET_DEV='1x0000000000000000000000000000000AA'

//used for email alerts and contact form, follow instructions
EMAIL_HOST='smtp.gmail.com'
EMAIL_PORT=<port>
EMAIL_USER=<gmail-account>
EMAIL_PASSWORD=<app-password> //Generate a separata app password from gmail settings

JWT_SECRET_KEY=<generate-a-secret> //google how to generate a jwt secret key
FERNET_KEY=<fernet-key> // run 'Fernet.generate_key()' in python and print the key
```


#### Cron

Use linux for a cronjob (WSL for windows).

`crontab -e`

add the job lines at the bottom after the comments

`*/5 * * * * /path/to/project.../ip-lookup/cloudflare.sh >> /path/to/project.../ip-lookup/cron_task.log 2>&1`
`@reboot /path/to/project.../ip-lookup/cloudflare.sh >> /path/to/project.../ip-lookup/cron_task.log 2>&1`

Then

`sudo service cron start`

Running in AWS: `sudo systemctl start crond`

if permission issues

`chmod +x /path/to/project.../ip-lookup/cloudflare.sh`

##### Logging in Cloudwatch: 

`sudo nano /opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json`

```
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/home/.../cron_task.log",
                        "log_group_name": "cron-logs",
                        "log_stream_name": "cloudflare-cron-logs",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    }
}
```

finally

```
sudo amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/cloudwatch-config.json \
    -s
```

## AI

Current version:

![image](https://github.com/user-attachments/assets/dee0ed12-fd24-4631-bcc1-dc1ad97f3e78)

- _LLM = function uses primarily an LLM call for logic
- _FUNC = no LLM calls

No agentic behaviour, straight line graph. This is because in my experience, smaller models really suck at tool calling.
Also with rate limits, I live in fear that free tier limits will kill agentic use

The linear model uses ~600 total tokens per request.

Router performs well with `deepseek-r1-distill-llama-70b`, have to re-think to get to a smaller model / model with larger rate limits

###  Agentic

Can the system be designed such that there is an agent (or agents) who make very specific Maps API calls?

Main benefit would be that the search can include a lot of detail.

For example:

We want to enjoy the EURO games outside with cocktails ->

outdoorSeating

liveMusic	

menuForChildren	

servesCocktails	

servesDessert

servesCoffee

goodForChildren

allowsDogs

restroom

goodForGroups

goodForWatchingSports



Can be queried specifically to produce answers.


Example:

input -> Agent/multiagent system ->

with search tools:

infer request and parametrizise places id query ->

save info + vectorize if needed (reviews etc)

with ranking tools:

come up with 3-9 restaurants that best match what the user wants ->

save and ask for human feedback!

Display a sort-of-hidden chat window sith state[messages] where users can correct the system, keep state channels for the main logic hidden until output comes to the cards.

#### Downsides

Token usage and Maps API usage. If the systems starts using 10k tokens or more per query and uses 100 different calls to Maps, its a lot.

Must be tested if it is doable. If free rate limits get used with one or two queries, needs to be a paid service or just for me.

## Troubleshooting

#### Line endings

Adding stuff to .env file in Windows (VScode etc.) introduces Windows line endings and break things.

Run `cat -A .env` and look for ^M (indicating Windows line endings).

In WSL run 

`cd /path/to/env`

`sed -i 's/\r$//' .env`

#### ECS

Use 'bridge' network mode

If providing .env file in s3, remember to **not include** '' quotation marks in values

#### Emailer

Check logs if getting "SSL: CERTIFICATE_VERIFY_FAILED certificate verify failed: unable to get local issuer certificate "

Try without to see if the issue is on EC2 end: `ssl_context = ssl._create_unverified_context()`



