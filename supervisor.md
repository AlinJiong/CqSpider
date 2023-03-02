# supervisor 使用方法

## 安装

- pip 安装

  `pip install supervisor`
- 安装好之后，创建目录

  `mkdir /etc/supervisor`

  `echo_supervisord_conf > /etc/supervisor/supervisord.conf`
- 修改默认的配置文件 `supervisord.conf`
  `[include] files = /etc/supervisor/conf.d/*.conf`

## 启动

指定默认配置文件启动

`supervisord -c /etc/supervisor/supervisord.conf`

或者直接启动

`supervisord`

## 配置文件

```bash
[program:spider]
directory=/home/T1/CqSpider
command=python /home/T1/CqSpider/all.py
priority=999                ; the relative start priority (default 999)
autostart=true              ; start at supervisord start (default: true)
autorestart=true            ; retstart at unexpected quit (default: true)
startsecs=10                ; number of secs prog must stay running (def. 10)
startretries=3              ; max # of serial start failures (default 3)
exitcodes=0,2               ; 'expected' exit codes for process (default 0,2)
stopsignal=QUIT             ; signal used to kill process (default TERM)
stopwaitsecs=10             ; max num secs to wait before SIGKILL (default 10)
user=root                 ; setuid to this UNIX account to run the program
log_stdout=true
log_stderr=true             ; if true, log program stderr (def false)
logfile=/home/T1/CqSpider/all_py.log
logfile_maxbytes=1MB        ; max # logfile bytes b4 rotation (default 50MB)
logfile_backups=10          ; # of logfile backups (default 10)
stdout_logfile_maxbytes=50MB  ; stdout 日志文件大小，默认 50MB
stdout_logfile_backups=20     ; stdout 日志文件备份数
stdout_logfile=/home/T1/CqSpider/.stdout.log
```

## 常用命令

`supervisorctl reload # 重新启动supervisord`

`supervisorctl shutdown # 关闭supervisord`

`supervisorctl reread # 重新读取配置`

`supervisorctl update # 更新配置`

`supervisorctl restart spider # 重启 spider`

`supervisorctl status # 查看运行情况`

`supervisordctl start 进程名 # 启动进程`

`supervisordctl stop 进程名 # 关闭进程`

`supervisordctl restart 进程名 # 重启进程`

`supervisordctl clear 进程名 # 清空进程日志`
