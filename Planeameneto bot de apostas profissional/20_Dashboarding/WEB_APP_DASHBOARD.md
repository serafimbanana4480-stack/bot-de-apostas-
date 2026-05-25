# Web App e Dashboard Funcional

**ID:** `WEB-001` | **Fase:** #phase/4-8 | **Owner:** Full Stack Developer | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Aplicação web com dashboards interativos para visualização de predições, PnL, CLV, e performance de modelos. Baseado na implementação Flask do projeto kyleskom/NBA-ML-Betting e no web app do NBA-Betting.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Interface visual para monitorização e operação do sistema |
| **Framework** | FastAPI (backend) + React (frontend) |
| **Dashboards** | Predições, PnL, CLV, Performance do Modelo |
| **Autenticação** | JWT + OAuth2 |
| **Deploy** | Docker + Nginx |
| **Custo** | 0€ (stack 100% open-source) |

---

## 2. ARQUITETURA DO WEB APP

### 2.1 Stack Tecnológico

| Camada | Tecnologia | Versão |
|-------|-----------|--------|
| **Backend** | FastAPI | 0.104+ |
| **Frontend** | React + TypeScript | 18+ |
| **UI Library** | shadcn/ui | Latest |
| **Charts** | Recharts | Latest |
| **Database** | PostgreSQL | 15+ |
| **Cache** | Redis | 7+ |
| **Auth** | JWT + OAuth2 | - |
| **Deploy** | Docker + Nginx | Latest |

### 2.2 Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                   │
│              (SSL, Static Files, Load Balancing)            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  (REST API, WebSocket, Business Logic)                     │
├─────────────────────────────────────────────────────────────┤
│  • /api/predictions   → Predições do dia                    │
│  • /api/pnl           → PnL histórico                      │
│  • /api/clv           → CLV tracking                        │
│  • /api/model         → Performance do modelo               │
│  • /api/system        → Status do sistema                   │
│  • /ws/notifications → WebSocket para updates em tempo real│
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL + Redis                         │
│  (Dados persistentes + Cache)                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                            │
│  (Dashboards, Gráficos, Tabelas Interativas)               │
├─────────────────────────────────────────────────────────────┤
│  • /predictions      → Dashboard de predições              │
│  • /pnl              → Dashboard de PnL                    │
│  • /clv              → Dashboard de CLV                    │
│  • /model            → Dashboard de performance           │
│  • /system           → Dashboard de sistema               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. DASHBOARD DE PREDIÇÕES (LIVE)

### 3.1 Componentes

```typescript
// components/PredictionsDashboard.tsx
interface Prediction {
  game_id: string;
  home_team: string;
  away_team: string;
  market: string;
  selection: string;
  probability: number;
  edge: number;
  odds: number;
  stake_pct: number;
  status: 'pending' | 'approved' | 'rejected';
  game_time: string;
}

export const PredictionsDashboard = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPredictions();
    // WebSocket para updates em tempo real
    const ws = new WebSocket('ws://localhost:8000/ws/notifications');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_prediction') {
        setPredictions(prev => [...prev, data.prediction]);
      }
    };
    return () => ws.close();
  }, []);

  const fetchPredictions = async () => {
    const response = await fetch('/api/predictions/today');
    const data = await response.json();
    setPredictions(data.predictions);
    setLoading(false);
  };

  if (loading) return <div>Carregando...</div>;

  return (
    <div className="predictions-dashboard">
      <h1>Predições do Dia</h1>
      
      <div className="summary-cards">
        <SummaryCard 
          title="Sinais Gerados" 
          value={predictions.length} 
          icon="📊"
        />
        <SummaryCard 
          title="Aprovados" 
          value={predictions.filter(p => p.status === 'approved').length}
          icon="✅"
        />
        <SummaryCard 
          title="Edge Médio" 
          value={`${(predictions.reduce((acc, p) => acc + p.edge, 0) / predictions.length * 100).toFixed(1)}%`}
          icon="📈"
        />
      </div>

      <PredictionsTable predictions={predictions} />
    </div>
  );
};
```

### 3.2 Tabela de Predições

```typescript
const PredictionsTable = ({ predictions }: { predictions: Prediction[] }) => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Jogo</TableHead>
          <TableHead>Mercado</TableHead>
          <TableHead>Prob</TableHead>
          <TableHead>Edge</TableHead>
          <TableHead>Odd</TableHead>
          <TableHead>Stake</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {predictions.map((pred) => (
          <TableRow key={pred.game_id}>
            <TableCell>
              <div>
                <div className="font-medium">{pred.home_team}</div>
                <div className="text-sm text-gray-500">vs {pred.away_team}</div>
              </div>
            </TableCell>
            <TableCell>{pred.market}</TableCell>
            <TableCell>{(pred.probability * 100).toFixed(1)}%</TableCell>
            <TableCell>
              <Badge variant={pred.edge > 0.05 ? 'success' : 'default'}>
                {(pred.edge * 100).toFixed(1)}%
              </Badge>
            </TableCell>
            <TableCell>{pred.odds.toFixed(2)}</TableCell>
            <TableCell>{pred.stake_pct.toFixed(2)}%</TableCell>
            <TableCell>
              <Badge variant={pred.status === 'approved' ? 'success' : 'secondary'}>
                {pred.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
```

---

## 4. DASHBOARD DE PNL (HISTÓRICO)

### 4.1 Gráficos de PnL

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PnLData {
  date: string;
  pnl: number;
  cumulative: number;
  bets: number;
  win_rate: number;
}

export const PnLDashboard = () => {
  const [pnlData, setPnLData] = useState<PnLData[]>([]);
  const [period, setPeriod] = useState('30d');

  useEffect(() => {
    fetch(`/api/pnl/history?period=${period}`)
      .then(res => res.json())
      .then(data => setPnLData(data.pnl_history));
  }, [period]);

  return (
    <div className="pnl-dashboard">
      <h1>PnL Histórico</h1>
      
      <div className="period-selector">
        <Button variant={period === '7d' ? 'default' : 'outline'} onClick={() => setPeriod('7d')}>
          7 Dias
        </Button>
        <Button variant={period === '30d' ? 'default' : 'outline'} onClick={() => setPeriod('30d')}>
          30 Dias
        </Button>
        <Button variant={period === '90d' ? 'default' : 'outline'} onClick={() => setPeriod('90d')}>
          90 Dias
        </Button>
      </div>

      <div className="summary-cards">
        <SummaryCard 
          title="PnL Acumulado" 
          value={`€${pnlData[pnlData.length - 1]?.cumulative.toFixed(2) || '0.00'}`}
          icon="💰"
          trend={pnlData[pnlData.length - 1]?.cumulative > 0 ? 'up' : 'down'}
        />
        <SummaryCard 
          title="ROI" 
          value={`${((pnlData[pnlData.length - 1]?.cumulative / 10000) * 100).toFixed(1)}%`}
          icon="📈"
        />
        <SummaryCard 
          title="Hit Rate" 
          value={`${pnlData[pnlData.length - 1]?.win_rate.toFixed(1)}%`}
          icon="🎯"
        />
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={pnlData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="cumulative" 
            stroke="#8884d8" 
            name="PnL Acumulado (€)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

---

## 5. DASHBOARD DE CLV (TRACKING)

### 5.1 Métricas de CLV

```typescript
interface CLVMetrics {
  average_clv: number;
  clv_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
  clv_by_market: {
    moneyline: number;
    spread: number;
    total: number;
  };
}

export const CLVDashboard = () => {
  const [clvMetrics, setCLVMetrics] = useState<CLVMetrics | null>(null);

  useEffect(() => {
    fetch('/api/clv/metrics?days=30')
      .then(res => res.json())
      .then(data => setCLVMetrics(data));
  }, []);

  if (!clvMetrics) return <div>Carregando...</div>;

  return (
    <div className="clv-dashboard">
      <h1>CLV Tracking</h1>
      
      <div className="summary-cards">
        <SummaryCard 
          title="CLV Médio" 
          value={`${clvMetrics.average_clv.toFixed(2)}%`}
          icon="📊"
          trend={clvMetrics.average_clv > 0 ? 'up' : 'down'}
        />
        <SummaryCard 
          title="CLV Positivo" 
          value={`${clvMetrics.clv_distribution.positive.toFixed(1)}%`}
          icon="✅"
        />
        <SummaryCard 
          title="CLV Negativo" 
          value={`${clvMetrics.clv_distribution.negative.toFixed(1)}%`}
          icon="❌"
        />
      </div>

      <CLVByMarketChart data={clvMetrics.clv_by_market} />
    </div>
  );
};
```

---

## 6. DASHBOARD DE PERFORMANCE DO MODELO

### 6.1 Métricas de Modelo

```typescript
interface ModelPerformance {
  model_name: string;
  version: string;
  log_loss: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  calibration_score: number;
  last_trained: string;
}

export const ModelDashboard = () => {
  const [performance, setPerformance] = useState<ModelPerformance | null>(null);

  useEffect(() => {
    fetch('/api/model/performance')
      .then(res => res.json())
      .then(data => setPerformance(data));
  }, []);

  if (!performance) return <div>Carregando...</div>;

  return (
    <div className="model-dashboard">
      <h1>Performance do Modelo</h1>
      
      <div className="model-info">
        <h2>{performance.model_name} v{performance.version}</h2>
        <p className="text-sm text-gray-500">
          Último treino: {new Date(performance.last_trained).toLocaleString()}
        </p>
      </div>

      <div className="metrics-grid">
        <MetricCard 
          title="Log Loss" 
          value={performance.log_loss.toFixed(4)}
          target="< 0.65"
          status={performance.log_loss < 0.65 ? 'good' : 'warning'}
        />
        <MetricCard 
          title="Accuracy" 
          value={`${(performance.accuracy * 100).toFixed(1)}%`}
          target="> 55%"
          status={performance.accuracy > 0.55 ? 'good' : 'warning'}
        />
        <MetricCard 
          title="Precision" 
          value={`${(performance.precision * 100).toFixed(1)}%`}
          target="> 55%"
          status={performance.precision > 0.55 ? 'good' : 'warning'}
        />
        <MetricCard 
          title="Recall" 
          value={`${(performance.recall * 100).toFixed(1)}%`}
          target="> 50%"
          status={performance.recall > 0.50 ? 'good' : 'warning'}
        />
        <MetricCard 
          title="F1 Score" 
          value={performance.f1_score.toFixed(3)}
          target="> 0.52"
          status={performance.f1_score > 0.52 ? 'good' : 'warning'}
        />
        <MetricCard 
          title="Calibration" 
          value={performance.calibration_score.toFixed(3)}
          target="> 0.90"
          status={performance.calibration_score > 0.90 ? 'good' : 'warning'}
        />
      </div>

      <CalibrationChart />
    </div>
  );
};
```

---

## 7. DASHBOARD DE SISTEMA

### 7.1 Status dos Componentes

```typescript
interface SystemStatus {
  postgresql: { status: 'up' | 'down'; latency: number };
  redis: { status: 'up' | 'down'; latency: number };
  api: { status: 'up' | 'down'; latency: number };
  telegram_bot: { status: 'up' | 'down' };
  last_ingestion: string;
  last_prediction: string;
  bankroll: number;
  bankroll_peak: number;
  drawdown: number;
}

export const SystemDashboard = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    // Poll a cada 30 segundos
    const interval = setInterval(() => {
      fetch('/api/system/status')
        .then(res => res.json())
        .then(data => setStatus(data));
    }, 30000);

    fetch('/api/system/status')
      .then(res => res.json())
      .then(data => setStatus(data));

    return () => clearInterval(interval);
  }, []);

  if (!status) return <div>Carregando...</div>;

  return (
    <div className="system-dashboard">
      <h1>Status do Sistema</h1>
      
      <div className="components-status">
        <ComponentStatus 
          name="PostgreSQL" 
          status={status.postgresql.status}
          latency={status.postgresql.latency}
        />
        <ComponentStatus 
          name="Redis" 
          status={status.redis.status}
          latency={status.redis.latency}
        />
        <ComponentStatus 
          name="API" 
          status={status.api.status}
          latency={status.api.latency}
        />
        <ComponentStatus 
          name="Telegram Bot" 
          status={status.telegram_bot.status}
        />
      </div>

      <div className="bankroll-info">
        <h2>Banca</h2>
        <div className="bankroll-cards">
          <Card>
            <CardHeader>Banca Atual</CardHeader>
            <CardContent>€{status.bankroll.toFixed(2)}</CardContent>
          </Card>
          <Card>
            <CardHeader>Banca Pico</CardHeader>
            <CardContent>€{status.bankroll_peak.toFixed(2)}</CardContent>
          </Card>
          <Card>
            <CardHeader>Drawdown</CardHeader>
            <CardContent className={status.drawdown > 10 ? 'text-red-500' : 'text-green-500'}>
              {status.drawdown.toFixed(2)}%
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
```

---

## 8. AUTENTICAÇÃO E SEGURANÇA

### 8.1 JWT Authentication

```python
# backend/auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 8.2 OAuth2 Integration

```python
# backend/auth/oauth.py
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    return payload
```

---

## 9. DEPLOY E INFRAESTRUTURA

### 9.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://vbq:vbq_password@postgres:5432/vbq
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=your-secret-key
    volumes:
      - ./backend:/app

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=vbq
      - POSTGRES_PASSWORD=vbq_password
      - POSTGRES_DB=vbq
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 9.2 Nginx Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name vbq.local;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 10. API ENDPOINTS

### 10.1 Backend Endpoints

```python
# backend/main.py
from fastapi import FastAPI, Depends
from backend.auth.oauth import get_current_user

app = FastAPI(title="VBQ Value Betting API")

@app.get("/api/predictions/today")
async def get_predictions_today(user = Depends(get_current_user)):
    """Retorna predições do dia atual."""
    predictions = get_predictions_from_db(date=datetime.now().date())
    return {"predictions": predictions}

@app.get("/api/pnl/history")
async def get_pnl_history(period: str = "30d", user = Depends(get_current_user)):
    """Retorna histórico de PnL."""
    pnl_history = calculate_pnl_history(period)
    return {"pnl_history": pnl_history}

@app.get("/api/clv/metrics")
async def get_clv_metrics(days: int = 30, user = Depends(get_current_user)):
    """Retorna métricas de CLV."""
    clv_metrics = calculate_clv_metrics(days)
    return clv_metrics

@app.get("/api/model/performance")
async def get_model_performance(user = Depends(get_current_user)):
    """Retorna performance do modelo atual."""
    performance = get_model_performance()
    return performance

@app.get("/api/system/status")
async def get_system_status(user = Depends(get_current_user)):
    """Retorna status do sistema."""
    status = get_system_status()
    return status

@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket para notificações em tempo real."""
    await websocket.accept()
    while True:
        # Enviar updates de predições
        new_predictions = get_new_predictions()
        await websocket.send_json({
            "type": "new_prediction",
            "prediction": new_predictions
        })
        await asyncio.sleep(30)  # Poll a cada 30 segundos
```

---

## 11. MONITORIZAÇÃO

### 11.1 Métricas do Web App

| Métrica | Descrição | Threshold |
|---------|-----------|-----------|
| webapp_response_time | Tempo de resposta API | < 500ms |
| webapp_error_rate | Taxa de erros | < 1% |
| webapp_active_users | Utilizadores ativos | - |
| websocket_connections | Conexões WebSocket | - |

---

## 12. EXEMPLOS DE CÓDIGO

### 12.1 Backend Main

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import predictions, pnl, clv, model, system

app = FastAPI(title="VBQ API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(pnl.router, prefix="/api/pnl", tags=["pnl"])
app.include_router(clv.router, prefix="/api/clv", tags=["clv"])
app.include_router(model.router, prefix="/api/model", tags=["model"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 13. TROUBLESHOOTING

### 13.1 Frontend Não Conecta ao Backend

```bash
# Verificar se backend está a correr
docker compose ps backend

# Verificar logs
docker compose logs backend

# Verificar CORS
# Editar backend/main.py: allow_origins=["http://localhost:3000"]
```

### 13.2 WebSocket Não Recebe Updates

```bash
# Verificar se WebSocket endpoint está acessível
wscat -c ws://localhost:8000/ws/notifications

# Verificar logs do backend
docker compose logs backend
```

---

## 14. LINKS CRUZADOS

- [[20_Dashboarding/INDEX]] ← Secção mãe
- [[09_Execution_System/CLI_OPERACOES_DIARIAS]] → CLI vs Web App
- [[35_Financial_Tracking/PLANILHA_PnL_COMPLETO]] → Fonte de dados PnL
- [[37_CLV_Analytics/ANALISE_CLV_COMPLETO]] → Fonte de dados CLV
- [[10_Infrastructure/MONITORIZACAO_INFRA]] → Monitorização

---

**Custo de implementação:** 0€ (FastAPI, React, shadcn/ui são open-source)  
**Tempo estimado de implementação:** 2-3 semanas  
**Prioridade:** ALTA (fundamental para operação visual do sistema)
