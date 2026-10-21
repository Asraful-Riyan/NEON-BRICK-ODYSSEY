import sys, subprocess, importlib.util

def ensure_pygame():
    if importlib.util.find_spec('pygame') is None:
        print('Installing pygame automatically...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pygame>=2.5,<3'])
ensure_pygame()

import pygame, random, math, json
from pathlib import Path
pygame.init()
W,H=1100,760
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption('NEON BRICK ODYSSEY')
clock=pygame.time.Clock()
FONT=pygame.font.SysFont('consolas',22,bold=True)
SMALL=pygame.font.SysFont('consolas',16)
BIG=pygame.font.SysFont('consolas',60,bold=True)
SAVE=Path.home()/'.neon_brick_odyssey.json'
try: best=json.loads(SAVE.read_text()).get('best',0)
except Exception: best=0
COLORS=[(0,240,255),(255,67,169),(165,103,255),(255,197,63),(70,255,163)]
stars=[(random.randrange(W),random.randrange(H),random.uniform(.4,2.3)) for _ in range(115)]
particles=[]; balls=[]; bricks=[]; powers=[]
score=0; lives=3; level=1; combo=0; state='menu'; paddle_x=W/2; paddle_w=132; shield=0; slow=0; magnet=0; shake=0

def text(s,x,y,font=FONT,color=(230,240,255),center=False):
    img=font.render(str(s),True,color); rect=img.get_rect(); rect.center=(x,y) if center else (x+rect.w/2,y+rect.h/2); screen.blit(img,rect)
def glow_circle(x,y,r,c):
    for k in (3,2,1):
        surf=pygame.Surface((int(r*7),int(r*7)),pygame.SRCALPHA)
        pygame.draw.circle(surf,(*c,10+k*6),(surf.get_width()//2,)*2,int(r+k*7))
        screen.blit(surf,(x-surf.get_width()/2,y-surf.get_height()/2))
    pygame.draw.circle(screen,c,(int(x),int(y)),int(r))
def burst(x,y,c,n=15):
    for _ in range(n):
        a=random.random()*math.tau; v=random.uniform(1,6)
        particles.append([x,y,math.cos(a)*v,math.sin(a)*v,random.randint(15,35),c])
def new_ball(stuck=True):
    balls.append({'x':paddle_x,'y':H-78,'vx':random.choice([-4,4]),'vy':-6,'r':9,'stuck':stuck,'trail':[]})
def build_level():
    bricks.clear(); rows=min(5+level,9); cols=12; bw=75; gap=9; left=(W-(cols*(bw+gap)-gap))/2
    for row in range(rows):
        for col in range(cols):
            if level>1 and (row*3+col*7+level)%13==0: continue
            hp=1+(row+level-1)//4
            bricks.append({'rect':pygame.Rect(int(left+col*(bw+gap)),115+row*36,bw,26),'hp':hp,'max':hp,'color':COLORS[(row+col//3)%len(COLORS)]})
def reset_game():
    global score,lives,level,combo,paddle_w,shield,slow,magnet,state
    score=0;lives=3;level=1;combo=0;paddle_w=132;shield=0;slow=0;magnet=0;state='playing';balls.clear();powers.clear();particles.clear();build_level();new_ball()
def power_drop(x,y):
    if random.random()<.17: powers.append({'x':x,'y':y,'kind':random.choice(['WIDE','MULTI','SHIELD','SLOW','MAGNET']),'phase':0})
def apply_power(kind):
    global paddle_w,shield,slow,magnet
    if kind=='WIDE': paddle_w=min(235,paddle_w+40)
    elif kind=='MULTI':
        for b in balls[:3]:
            if not b['stuck']:
                for delta in (-.45,.45):
                    angle=math.atan2(b['vy'],b['vx'])+delta
                    balls.append({'x':b['x'],'y':b['y'],'vx':math.cos(angle)*7,'vy':math.sin(angle)*7,'r':9,'stuck':False,'trail':[]})
    elif kind=='SHIELD': shield=700
    elif kind=='SLOW': slow=550
    elif kind=='MAGNET': magnet=550

def update(dt):
    global paddle_x,score,combo,lives,level,state,shield,slow,magnet,shake,best
    mx=pygame.mouse.get_pos()[0]; keys=pygame.key.get_pressed()
    target=mx if pygame.mouse.get_focused() else paddle_x+(keys[pygame.K_RIGHT]-keys[pygame.K_LEFT])*13
    paddle_x+= (max(paddle_w/2+12,min(W-paddle_w/2-12,target))-paddle_x)*min(1,.22*dt)
    if shield:shield=max(0,shield-dt)
    if slow:slow=max(0,slow-dt)
    if magnet:magnet=max(0,magnet-dt)
    if shake:shake=max(0,shake-dt)
    pad=pygame.Rect(int(paddle_x-paddle_w/2),H-65,int(paddle_w),17)
    for p in powers[:]:
        p['y']+=2.7*dt;p['phase']+=.05*dt
        if pad.collidepoint(p['x'],p['y']+13):apply_power(p['kind']);burst(p['x'],p['y'],(255,255,255));powers.remove(p)
        elif p['y']>H:powers.remove(p)
    for b in balls[:]:
        if b['stuck']:
            b['x']=paddle_x;b['y']=H-79;continue
        b['trail'].append((b['x'],b['y']));b['trail']=b['trail'][-12:]
        step=.76 if slow else 1
        prevx,prevy=b['x'],b['y']
        b['x']+=b['vx']*dt*step;b['y']+=b['vy']*dt*step
        if b['x']<b['r'] or b['x']>W-b['r']:b['vx']*=-1;b['x']=max(b['r'],min(W-b['r'],b['x']))
        if b['y']<55:b['vy']=abs(b['vy'])
        if b['vy']>0 and pad.collidepoint(b['x'],b['y']+b['r']) and prevy<=pad.top:
            offset=(b['x']-paddle_x)/(paddle_w/2); speed=min(10.5,math.hypot(b['vx'],b['vy'])+.07)
            b['vx']=speed*math.sin(offset*1.13);b['vy']=-max(3.4,speed*math.cos(offset*1.13));b['y']=pad.top-b['r'];combo=0
            burst(b['x'],b['y'],(0,230,255),5)
            if magnet:b['stuck']=True
        hit=None
        for brick in bricks:
            if brick['rect'].inflate(b['r']*2,b['r']*2).collidepoint(b['x'],b['y']):hit=brick;break
        if hit:
            r=hit['rect']
            if prevx<r.left-b['r'] or prevx>r.right+b['r']:b['vx']*=-1
            else:b['vy']*=-1
            hit['hp']-=1;burst(b['x'],b['y'],hit['color'],9)
            if hit['hp']<=0:
                bricks.remove(hit);combo+=1;score+=100+min(combo,15)*15;power_drop(r.centerx,r.centery)
                if score>best:
                    best=score
                    try:SAVE.write_text(json.dumps({'best':best}))
                    except OSError:pass
        if b['y']>H+20:
            if shield:
                b['y']=H-100;b['vy']=-abs(b['vy']);shield=0
            else:balls.remove(b)
    if not balls:
        lives-=1;combo=0
        if lives<=0:state='gameover'
        else:new_ball()
    if not bricks:
        level+=1;balls.clear();powers.clear();build_level();new_ball();state='levelup'
    for p in particles[:]:
        p[0]+=p[2]*dt;p[1]+=p[3]*dt;p[4]-=dt
        if p[4]<=0:particles.remove(p)

def draw():
    screen.fill((6,8,23))
    t=pygame.time.get_ticks()/1000
    for i in range(0,H,38):pygame.draw.line(screen,(12,18,38),(0,i),(W,i),1)
    for x,y,z in stars:
        yy=(y+t*z*9)%H
        pygame.draw.circle(screen,(int(35+z*38),int(50+z*35),int(95+z*44)),(int(x),int(yy)),1 if z<1.5 else 2)
    for brick in bricks:
        r=brick['rect'];c=brick['color'];pygame.draw.rect(screen,tuple(v//5 for v in c),r.inflate(7,7),border_radius=8)
        pygame.draw.rect(screen,c,r,border_radius=6);pygame.draw.rect(screen,(245,245,255),(r.x+4,r.y+3,r.w-8,4),border_radius=3)
        if brick['hp']>1:text(str(brick['hp']),r.centerx,r.centery,SMALL,(12,15,30),True)
    for p in powers:
        c=(255,211,74);r=pygame.Rect(int(p['x']-29),int(p['y']-12),58,24)
        pygame.draw.rect(screen,(40,35,68),r,border_radius=7);pygame.draw.rect(screen,c,r,2,border_radius=7)
        text(p['kind'][:5],r.centerx,r.centery,SMALL,c,True)
    for b in balls:
        for i,(x,y) in enumerate(b['trail']):
            pygame.draw.circle(screen,(0,60+int(i*13),90+int(i*12)),(int(x),int(y)),max(2,int(b['r']*(i+1)/len(b['trail']))))
        glow_circle(b['x'],b['y'],b['r'],(170,248,255))
    pad=pygame.Rect(int(paddle_x-paddle_w/2),H-65,int(paddle_w),17)
    pygame.draw.rect(screen,(0,58,80),pad.inflate(14,16),border_radius=12)
    pygame.draw.rect(screen,(0,235,255),pad,border_radius=9)
    pygame.draw.rect(screen,(210,255,255),(pad.x+8,pad.y+2,pad.w-16,4),border_radius=3)
    if shield:pygame.draw.line(screen,(255,200,68),(0,H-18),(W,H-18),4)
    for x,y,vx,vy,life,c in particles:
        pygame.draw.circle(screen,c,(int(x),int(y)),max(1,int(life/12)))
    text(f'SCORE  {score:07d}',24,18);text(f'BEST  {best:07d}',365,18);text(f'LEVEL  {level}',700,18);text(f'LIVES  {lives}',920,18)
    pygame.draw.line(screen,(30,80,110),(0,49),(W,49),2)
    active=[name for name,ttl in [('SHIELD',shield),('SLOW',slow),('MAGNET',magnet)] if ttl]
    if active:text('ACTIVE: '+', '.join(active),18,H-27,SMALL,(250,213,100))
    if state!='playing':
        overlay=pygame.Surface((W,H),pygame.SRCALPHA);overlay.fill((3,6,19,205));screen.blit(overlay,(0,0))
        if state=='menu':
            text('NEON BRICK',W/2,235,BIG,(0,235,255),True)
            text('ODYSSEY',W/2,305,BIG,(255,72,174),True)
            text('BREAK BRICKS  •  COLLECT POWERS  •  CHASE COMBOS',W/2,393,SMALL,(220,220,245),True)
            text('CLICK OR PRESS SPACE TO START',W/2,475,FONT,(255,218,95),True)
            text('Mouse: Move  |  Click/Space: Launch  |  P: Pause  |  R: Restart  |  ESC: Menu',W/2,550,SMALL,(155,175,205),True)
        elif state=='paused':text('PAUSED',W/2,315,BIG,(255,215,90),True);text('PRESS P TO RESUME',W/2,400,FONT,center=True)
        elif state=='gameover':text('GAME OVER',W/2,300,BIG,(255,80,140),True);text(f'FINAL SCORE: {score}',W/2,395,FONT,center=True);text('PRESS SPACE TO TRY AGAIN',W/2,470,FONT,center=True)
        elif state=='levelup':text(f'LEVEL {level}',W/2,300,BIG,(0,240,255),True);text('PRESS SPACE FOR THE NEXT WAVE',W/2,410,FONT,center=True)
    pygame.display.flip()

running=True
while running:
    dt=min(clock.tick(60)/16.6667,2)
    for e in pygame.event.get():
        if e.type==pygame.QUIT:running=False
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE:state='menu'
            elif e.key==pygame.K_r:reset_game()
            elif e.key==pygame.K_p:state='paused' if state=='playing' else 'playing' if state=='paused' else state
            elif e.key==pygame.K_SPACE:
                if state in ('menu','gameover'):reset_game()
                elif state=='levelup':state='playing'
                elif state=='playing':
                    for b in balls:b['stuck']=False
        elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            if state in ('menu','gameover'):reset_game()
            elif state=='levelup':state='playing'
            elif state=='playing':
                for b in balls:b['stuck']=False
    if state=='playing':update(dt)
    draw()
pygame.quit()
