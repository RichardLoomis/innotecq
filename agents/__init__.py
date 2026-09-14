from agents.ap_agent import AGENT as _ap
from agents.helpdesk_agent import AGENT as _helpdesk
from agents.reporting_agent import AGENT as _reporting
from agents.support_agent import AGENT as _support

AGENTS = {agent.key: agent for agent in (_ap, _helpdesk, _support, _reporting)}
