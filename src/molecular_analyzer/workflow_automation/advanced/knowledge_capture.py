#!/usr/bin/env python3
"""
Knowledge Capture System - Phase 3 Advanced Features

Implements intelligent decision capture, knowledge extraction, and management
capabilities for workflow automation enhancement.

Author: Workflow Automation System
Version: 3.0.0
Phase: 3 - Advanced Features
"""

import json
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import ast
import hashlib
import logging
from collections import defaultdict, Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DecisionRecord:
    """Represents a captured decision with metadata."""
    id: str
    timestamp: datetime
    decision_type: str
    description: str
    rationale: str
    context: Dict[str, Any]
    impact_level: str  # 'low', 'medium', 'high', 'critical'
    tags: List[str]
    source: str  # 'code', 'comment', 'documentation', 'session'
    confidence: float
    related_files: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionRecord':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class DecisionCaptureEngine:
    """Intelligently captures important decisions from various sources."""
    
    def __init__(self):
        self.decision_patterns = {
            'architectural': [
                r'(?:decided|choosing|selected|opted)\s+(?:to\s+)?(?:use|implement|adopt|go with)',
                r'architecture\s+(?:decision|choice|pattern)',
                r'design\s+(?:decision|pattern|choice)',
                r'we\s+(?:decided|chose|selected|will use)',
            ],
            'technical': [
                r'(?:refactor|restructure|optimize|performance)',
                r'(?:algorithm|approach|method)\s+(?:change|selection)',
                r'(?:library|framework|tool)\s+(?:change|selection|choice)',
                r'(?:deprecated|removed|replaced)\s+(?:because|due to)',
            ],
            'process': [
                r'(?:workflow|process|procedure)\s+(?:change|update|improvement)',
                r'(?:testing|deployment|integration)\s+(?:strategy|approach)',
                r'(?:coding|naming|style)\s+(?:standard|convention)',
                r'(?:review|approval|validation)\s+(?:process|procedure)',
            ],
            'business': [
                r'(?:requirement|feature|functionality)\s+(?:change|addition|removal)',
                r'(?:priority|timeline|deadline)\s+(?:change|adjustment)',
                r'(?:user|customer|stakeholder)\s+(?:feedback|request|demand)',
                r'(?:budget|resource|constraint)\s+(?:consideration|limitation)',
            ]
        }
        
        self.impact_indicators = {
            'critical': [
                'breaking change', 'major refactor', 'core architecture',
                'security', 'performance critical', 'data loss',
                'system-wide', 'fundamental change'
            ],
            'high': [
                'significant impact', 'multiple files', 'api change',
                'database schema', 'user interface', 'workflow change',
                'major feature', 'integration point'
            ],
            'medium': [
                'moderate impact', 'single module', 'configuration change',
                'minor feature', 'improvement', 'optimization',
                'code cleanup', 'documentation update'
            ],
            'low': [
                'typo fix', 'comment update', 'formatting',
                'variable rename', 'minor bug', 'style change',
                'log message', 'test update'
            ]
        }
        
        logger.info("DecisionCaptureEngine initialized")
    
    def capture_from_code(self, file_path: str) -> List[DecisionRecord]:
        """Capture decisions from code comments and docstrings."""
        decisions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse Python AST for structured analysis
            if file_path.endswith('.py'):
                decisions.extend(self._analyze_python_code(file_path, content))
            
            # Analyze comments for decision indicators
            decisions.extend(self._analyze_comments(file_path, content))
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return decisions
    
    def capture_from_session(self, session_data: Dict[str, Any]) -> List[DecisionRecord]:
        """Capture decisions from session interactions and outputs."""
        decisions = []
        
        try:
            # Analyze task completions for decisions
            if 'completed_tasks' in session_data:
                for task in session_data['completed_tasks']:
                    decision = self._extract_decision_from_task(task)
                    if decision:
                        decisions.append(decision)
            
            # Analyze conversation context for decisions
            if 'interactions' in session_data:
                decisions.extend(self._analyze_interactions(session_data['interactions']))
            
            # Analyze file changes for decisions
            if 'file_changes' in session_data:
                decisions.extend(self._analyze_file_changes(session_data['file_changes']))
                
        except Exception as e:
            logger.error(f"Error analyzing session data: {e}")
        
        return decisions
    
    def _analyze_python_code(self, file_path: str, content: str) -> List[DecisionRecord]:
        """Analyze Python code structure for architectural decisions."""
        decisions = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Analyze class definitions
                if isinstance(node, ast.ClassDef):
                    decision = self._analyze_class_definition(file_path, node)
                    if decision:
                        decisions.append(decision)
                
                # Analyze function definitions
                if isinstance(node, ast.FunctionDef):
                    decision = self._analyze_function_definition(file_path, node)
                    if decision:
                        decisions.append(decision)
                
                # Analyze imports for technology decisions
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    decision = self._analyze_import_statement(file_path, node)
                    if decision:
                        decisions.append(decision)
        
        except SyntaxError:
            logger.warning(f"Syntax error in {file_path}, skipping AST analysis")
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
        
        return decisions
    
    def _analyze_comments(self, file_path: str, content: str) -> List[DecisionRecord]:
        """Analyze comments for decision indicators."""
        decisions = []
        
        # Extract all comments
        comment_pattern = r'#\s*([^\r\n]*)'
        comments = re.findall(comment_pattern, content)
        
        for comment_text in comments:
            if len(comment_text.strip()) < 20:  # Skip short comments
                continue
                
            decision = self._extract_decision_from_text(
                text=comment_text,
                source='code',
                context={'file': file_path, 'type': 'comment'}
            )
            
            if decision:
                decisions.append(decision)
        
        return decisions
    
    def _extract_decision_from_text(self, text: str, source: str, context: Dict[str, Any]) -> Optional[DecisionRecord]:
        """Extract decision information from text using pattern matching."""
        text_lower = text.lower()
        
        # Check for decision patterns
        decision_type = None
        for d_type, patterns in self.decision_patterns.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                decision_type = d_type
                break
        
        if not decision_type:
            return None
        
        # Determine impact level
        impact_level = self._determine_impact_level(text_lower)
        
        # Extract tags
        tags = self._extract_tags(text)
        
        # Generate decision ID
        decision_id = hashlib.md5(f"{text}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Calculate confidence based on pattern strength and context
        confidence = self._calculate_confidence(text, decision_type, context)
        
        return DecisionRecord(
            id=decision_id,
            timestamp=datetime.now(),
            decision_type=decision_type,
            description=text.strip(),
            rationale=self._extract_rationale(text),
            context=context,
            impact_level=impact_level,
            tags=tags,
            source=source,
            confidence=confidence,
            related_files=[context.get('file', '')]
        )
    
    def _determine_impact_level(self, text: str) -> str:
        """Determine impact level based on text content."""
        text_lower = text.lower()
        
        # Count indicators for each level
        level_scores = {}
        for level in ['critical', 'high', 'medium', 'low']:
            indicators = self.impact_indicators[level]
            score = sum(1 for indicator in indicators if indicator in text_lower)
            level_scores[level] = score
        
        # Find the level with highest score
        max_score = max(level_scores.values())
        if max_score == 0:
            return 'low'  # Default for no indicators
        
        # Return the highest priority level with max score
        for level in ['critical', 'high', 'medium', 'low']:
            if level_scores[level] == max_score:
                return level
        
        return 'low'  # Fallback
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        
        # Technology tags
        tech_keywords = ['python', 'javascript', 'react', 'django', 'flask', 'numpy', 'pandas']
        for keyword in tech_keywords:
            if keyword in text.lower():
                tags.append(f'tech:{keyword}')
        
        # Action tags
        action_keywords = ['refactor', 'optimize', 'implement', 'remove', 'update', 'fix']
        for keyword in action_keywords:
            if keyword in text.lower():
                tags.append(f'action:{keyword}')
        
        # Domain tags
        domain_keywords = ['security', 'performance', 'ui', 'database', 'api', 'testing']
        for keyword in domain_keywords:
            if keyword in text.lower():
                tags.append(f'domain:{keyword}')
        
        return tags
    
    def _extract_rationale(self, text: str) -> str:
        """Extract rationale from decision text."""
        # Look for rationale indicators
        rationale_patterns = [
            r'because\s+(.+)',
            r'due\s+to\s+(.+)',
            r'reason[:\s]+(.+)',
            r'since\s+(.+)',
            r'as\s+(.+)',
        ]
        
        for pattern in rationale_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _calculate_confidence(self, text: str, decision_type: str, context: Dict[str, Any]) -> float:
        """Calculate confidence score for the decision detection."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on explicit decision keywords
        explicit_keywords = ['decided', 'choose', 'selected', 'opted', 'will use']
        if any(keyword in text.lower() for keyword in explicit_keywords):
            confidence += 0.2
        
        # Boost confidence based on rationale presence
        if self._extract_rationale(text):
            confidence += 0.15
        
        # Boost confidence based on context
        if context.get('type') == 'docstring':
            confidence += 0.1
        
        # Boost confidence based on text length and detail
        if len(text) > 50:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _analyze_class_definition(self, file_path: str, node: ast.ClassDef) -> Optional[DecisionRecord]:
        """Analyze class definition for architectural decisions."""
        # Check if class represents a significant architectural decision
        if node.name.endswith(('Engine', 'Manager', 'System', 'Handler', 'Controller')):
            return DecisionRecord(
                id=hashlib.md5(f"{file_path}_{node.name}".encode()).hexdigest()[:12],
                timestamp=datetime.now(),
                decision_type='architectural',
                description=f"Implemented {node.name} class in {Path(file_path).name}",
                rationale="Architectural component for system organization",
                context={'file': file_path, 'class': node.name, 'line': node.lineno},
                impact_level='medium',
                tags=['architecture', 'class-design'],
                source='code',
                confidence=0.7,
                related_files=[file_path]
            )
        return None
    
    def _analyze_function_definition(self, file_path: str, node: ast.FunctionDef) -> Optional[DecisionRecord]:
        """Analyze function definition for implementation decisions."""
        # Check docstring for decision information
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            docstring = node.body[0].value.s
            if len(docstring) > 50 and any(keyword in docstring.lower() 
                                         for keyword in ['decision', 'chose', 'implement', 'approach']):
                return self._extract_decision_from_text(
                    text=docstring,
                    source='code',
                    context={'file': file_path, 'function': node.name, 'line': node.lineno, 'type': 'docstring'}
                )
        return None
    
    def _analyze_import_statement(self, file_path: str, node) -> Optional[DecisionRecord]:
        """Analyze import statements for technology decisions."""
        # Skip standard library imports
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        else:  # ImportFrom
            modules = [node.module] if node.module else []
        
        # Look for significant third-party libraries
        significant_libraries = [
            'numpy', 'pandas', 'sklearn', 'tensorflow', 'pytorch',
            'django', 'flask', 'fastapi', 'requests', 'selenium',
            'matplotlib', 'plotly', 'streamlit', 'dash'
        ]
        
        for module in modules:
            if module and any(lib in module.lower() for lib in significant_libraries):
                return DecisionRecord(
                    id=hashlib.md5(f"{file_path}_import_{module}".encode()).hexdigest()[:12],
                    timestamp=datetime.now(),
                    decision_type='technical',
                    description=f"Adopted {module} library in {Path(file_path).name}",
                    rationale="Technology selection for project requirements",
                    context={'file': file_path, 'module': module, 'line': node.lineno},
                    impact_level='medium',
                    tags=[f'tech:{module.lower()}', 'library-adoption'],
                    source='code',
                    confidence=0.6,
                    related_files=[file_path]
                )
        return None
    
    def _extract_decision_from_task(self, task: Dict[str, Any]) -> Optional[DecisionRecord]:
        """Extract decision from completed task."""
        task_description = task.get('description', '')
        
        if len(task_description) < 20:
            return None
        
        return self._extract_decision_from_text(
            text=task_description,
            source='session',
            context={'task_id': task.get('id'), 'completion_time': task.get('completed_at')}
        )
    
    def _analyze_interactions(self, interactions: List[Dict[str, Any]]) -> List[DecisionRecord]:
        """Analyze conversation interactions for decisions."""
        decisions = []
        
        for interaction in interactions:
            if 'response' in interaction and len(interaction['response']) > 50:
                decision = self._extract_decision_from_text(
                    text=interaction['response'],
                    source='session',
                    context={'interaction_id': interaction.get('id'), 'type': 'conversation'}
                )
                if decision:
                    decisions.append(decision)
        
        return decisions
    
    def _analyze_file_changes(self, file_changes: List[Dict[str, Any]]) -> List[DecisionRecord]:
        """Analyze file changes for implementation decisions."""
        decisions = []
        
        for change in file_changes:
            if change.get('type') == 'major_refactor' or change.get('lines_changed', 0) > 50:
                decision = DecisionRecord(
                    id=hashlib.md5(f"change_{change.get('file')}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                    timestamp=datetime.now(),
                    decision_type='technical',
                    description=f"Major changes to {change.get('file')}",
                    rationale=change.get('rationale', 'Code improvement and maintenance'),
                    context=change,
                    impact_level='medium',
                    tags=['refactor', 'code-change'],
                    source='session',
                    confidence=0.7,
                    related_files=[change.get('file')]
                )
                decisions.append(decision)
        
        return decisions


class KnowledgeExtractor:
    """Extracts and classifies knowledge from decisions and content."""
    
    def __init__(self):
        self.classification_rules = {
            'patterns': {
                'best_practice': ['best practice', 'recommended approach', 'standard way', 'proven method'],
                'lesson_learned': ['learned that', 'discovered', 'found out', 'realized'],
                'pitfall': ['avoid', 'don\'t', 'mistake', 'error', 'problem with'],
                'optimization': ['faster', 'efficient', 'optimize', 'performance', 'improve'],
                'workaround': ['workaround', 'temporary', 'hack', 'quick fix'],
                'requirement': ['must', 'required', 'mandatory', 'essential', 'critical']
            }
        }
        logger.info("KnowledgeExtractor initialized")
    
    def extract_knowledge(self, decision: DecisionRecord) -> Dict[str, Any]:
        """Extract structured knowledge from a decision record."""
        knowledge = {
            'id': f"knowledge_{decision.id}",
            'source_decision': decision.id,
            'knowledge_type': self._classify_knowledge_type(decision),
            'key_concepts': self._extract_concepts(decision.description),
            'applicability': self._determine_applicability(decision),
            'relationships': self._find_relationships(decision),
            'quality_score': self._calculate_quality_score(decision),
            'extracted_at': datetime.now().isoformat(),
            'metadata': {
                'decision_type': decision.decision_type,
                'impact_level': decision.impact_level,
                'confidence': decision.confidence,
                'tags': decision.tags
            }
        }
        
        return knowledge
    
    def _classify_knowledge_type(self, decision: DecisionRecord) -> str:
        """Classify the type of knowledge contained in the decision."""
        text_lower = decision.description.lower()
        
        for knowledge_type, patterns in self.classification_rules['patterns'].items():
            if any(pattern in text_lower for pattern in patterns):
                return knowledge_type
        
        # Default classification based on decision type
        type_mapping = {
            'architectural': 'design_pattern',
            'technical': 'implementation_detail',
            'process': 'workflow_pattern',
            'business': 'requirement'
        }
        
        return type_mapping.get(decision.decision_type, 'general')
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from decision text."""
        # Simple concept extraction based on important terms
        concepts = []
        
        # Technical concepts
        tech_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', text)  # CamelCase
        concepts.extend([term.lower() for term in tech_terms if len(term) > 3])
        
        # Extract quoted terms
        quoted_terms = re.findall(r'"([^"]+)"', text)
        concepts.extend(quoted_terms)
        
        # Extract parenthetical explanations
        paren_terms = re.findall(r'\(([^)]+)\)', text)
        concepts.extend([term.strip() for term in paren_terms if len(term.strip()) > 3])
        
        return list(set(concepts))  # Remove duplicates
    
    def _determine_applicability(self, decision: DecisionRecord) -> Dict[str, Any]:
        """Determine where and when this knowledge is applicable."""
        return {
            'project_types': self._infer_project_types(decision),
            'contexts': decision.tags,
            'conditions': self._extract_conditions(decision.description),
            'scope': self._determine_scope(decision)
        }
    
    def _find_relationships(self, decision: DecisionRecord) -> List[str]:
        """Find relationships to other concepts or decisions."""
        relationships = []
        
        # Look for references to other components
        if decision.related_files:
            relationships.extend([f"file:{file}" for file in decision.related_files])
        
        # Look for technology relationships
        for tag in decision.tags:
            if tag.startswith('tech:'):
                relationships.append(f"technology:{tag[5:]}")
        
        return relationships
    
    def _calculate_quality_score(self, decision: DecisionRecord) -> float:
        """Calculate quality score for the extracted knowledge."""
        score = decision.confidence * 0.4  # Base from decision confidence
        
        # Boost for detailed rationale
        if len(decision.rationale) > 20:
            score += 0.2
        
        # Boost for high impact
        impact_boost = {'critical': 0.3, 'high': 0.2, 'medium': 0.1, 'low': 0.0}
        score += impact_boost.get(decision.impact_level, 0.0)
        
        # Boost for multiple tags (indicates rich context)
        if len(decision.tags) > 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _infer_project_types(self, decision: DecisionRecord) -> List[str]:
        """Infer applicable project types."""
        project_types = []
        
        # Infer from tags
        for tag in decision.tags:
            if tag.startswith('tech:'):
                tech = tag[5:]
                if tech in ['python', 'django', 'flask']:
                    project_types.append('web_development')
                elif tech in ['numpy', 'pandas', 'sklearn']:
                    project_types.append('data_science')
                elif tech in ['react', 'javascript']:
                    project_types.append('frontend_development')
        
        # Infer from file types
        for file_path in decision.related_files:
            if file_path.endswith('.py'):
                project_types.append('python_project')
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                project_types.append('javascript_project')
        
        return list(set(project_types))
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditions when the knowledge applies."""
        conditions = []
        
        # Look for conditional statements
        condition_patterns = [
            r'when\s+(.+?)(?:\.|,|$)',
            r'if\s+(.+?)(?:\.|,|$)',
            r'unless\s+(.+?)(?:\.|,|$)',
            r'provided\s+that\s+(.+?)(?:\.|,|$)'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text.lower())
            conditions.extend([match.strip() for match in matches])
        
        return conditions
    
    def _determine_scope(self, decision: DecisionRecord) -> str:
        """Determine the scope of applicability."""
        if decision.impact_level == 'critical':
            return 'system_wide'
        elif decision.impact_level == 'high':
            return 'module_wide'
        elif len(decision.related_files) > 1:
            return 'multi_file'
        else:
            return 'local'


class KnowledgeBaseIntegrator:
    """Integrates knowledge into a searchable database system."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Create in workflow automation directory
            base_path = Path(__file__).parent.parent
            db_path = base_path / "knowledge_base.db"
        
        self.db_path = db_path
        self._initialize_database()
        logger.info(f"KnowledgeBaseIntegrator initialized with database: {db_path}")
    
    def _initialize_database(self):
        """Initialize the SQLite database with required tables."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create decisions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    rationale TEXT,
                    impact_level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    context TEXT,  -- JSON
                    tags TEXT,     -- JSON
                    related_files TEXT  -- JSON
                )
            ''')
            
            # Create knowledge table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    source_decision TEXT NOT NULL,
                    knowledge_type TEXT NOT NULL,
                    key_concepts TEXT,  -- JSON
                    applicability TEXT,  -- JSON
                    relationships TEXT,  -- JSON
                    quality_score REAL NOT NULL,
                    extracted_at TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    FOREIGN KEY (source_decision) REFERENCES decisions (id)
                )
            ''')
            
            # Create search index for full-text search
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS decision_search USING fts5(
                    id,
                    description,
                    rationale,
                    tags,
                    content='decisions',
                    content_rowid='rowid'
                )
            ''')
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_decision(self, decision: DecisionRecord) -> bool:
        """Store a decision record in the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert decision
            cursor.execute('''
                INSERT OR REPLACE INTO decisions 
                (id, timestamp, decision_type, description, rationale, impact_level, 
                 source, confidence, context, tags, related_files)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision.id,
                decision.timestamp.isoformat(),
                decision.decision_type,
                decision.description,
                decision.rationale,
                decision.impact_level,
                decision.source,
                decision.confidence,
                json.dumps(decision.context),
                json.dumps(decision.tags),
                json.dumps(decision.related_files)
            ))
            
            # Update search index
            cursor.execute('''
                INSERT OR REPLACE INTO decision_search (id, description, rationale, tags)
                VALUES (?, ?, ?, ?)
            ''', (
                decision.id,
                decision.description,
                decision.rationale,
                ' '.join(decision.tags)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing decision {decision.id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def store_knowledge(self, knowledge: Dict[str, Any]) -> bool:
        """Store extracted knowledge in the database."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge
                (id, source_decision, knowledge_type, key_concepts, applicability,
                 relationships, quality_score, extracted_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                knowledge['id'],
                knowledge['source_decision'],
                knowledge['knowledge_type'],
                json.dumps(knowledge['key_concepts']),
                json.dumps(knowledge['applicability']),
                json.dumps(knowledge['relationships']),
                knowledge['quality_score'],
                knowledge['extracted_at'],
                json.dumps(knowledge['metadata'])
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing knowledge {knowledge['id']}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def search_decisions(self, query: str, limit: int = 10) -> List[DecisionRecord]:
        """Search decisions using full-text search."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Full-text search
                cursor.execute('''
                    SELECT d.* FROM decisions d
                    JOIN decision_search s ON d.id = s.id
                    WHERE decision_search MATCH ?
                    ORDER BY rank
                    LIMIT ?
                ''', (query, limit))
                
                results = []
                for row in cursor.fetchall():
                    decision_data = {
                        'id': row[0],
                        'timestamp': row[1],
                        'decision_type': row[2],
                        'description': row[3],
                        'rationale': row[4],
                        'impact_level': row[5],
                        'source': row[6],
                        'confidence': row[7],
                        'context': json.loads(row[8]) if row[8] else {},
                        'tags': json.loads(row[9]) if row[9] else [],
                        'related_files': json.loads(row[10]) if row[10] else []
                    }
                    results.append(DecisionRecord.from_dict(decision_data))
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching decisions: {e}")
            return []
    
    def get_knowledge_by_type(self, knowledge_type: str) -> List[Dict[str, Any]]:
        """Retrieve knowledge by type."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM knowledge
                    WHERE knowledge_type = ?
                    ORDER BY quality_score DESC
                ''', (knowledge_type,))
                
                results = []
                for row in cursor.fetchall():
                    knowledge = {
                        'id': row[0],
                        'source_decision': row[1],
                        'knowledge_type': row[2],
                        'key_concepts': json.loads(row[3]) if row[3] else [],
                        'applicability': json.loads(row[4]) if row[4] else {},
                        'relationships': json.loads(row[5]) if row[5] else [],
                        'quality_score': row[6],
                        'extracted_at': row[7],
                        'metadata': json.loads(row[8]) if row[8] else {}
                    }
                    results.append(knowledge)
                
                return results
                
        except Exception as e:
            logger.error(f"Error retrieving knowledge by type: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count decisions by type
                cursor.execute('''
                    SELECT decision_type, COUNT(*) as count
                    FROM decisions
                    GROUP BY decision_type
                ''')
                decision_counts = dict(cursor.fetchall())
                
                # Count knowledge by type
                cursor.execute('''
                    SELECT knowledge_type, COUNT(*) as count
                    FROM knowledge
                    GROUP BY knowledge_type
                ''')
                knowledge_counts = dict(cursor.fetchall())
                
                # Get total counts
                cursor.execute('SELECT COUNT(*) FROM decisions')
                total_decisions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM knowledge')
                total_knowledge = cursor.fetchone()[0]
                
                # Get quality distribution
                cursor.execute('''
                    SELECT 
                        CASE 
                            WHEN quality_score >= 0.8 THEN 'high'
                            WHEN quality_score >= 0.6 THEN 'medium'
                            ELSE 'low'
                        END as quality_tier,
                        COUNT(*) as count
                    FROM knowledge
                    GROUP BY quality_tier
                ''')
                quality_distribution = dict(cursor.fetchall())
                
                return {
                    'total_decisions': total_decisions,
                    'total_knowledge': total_knowledge,
                    'decisions_by_type': decision_counts,
                    'knowledge_by_type': knowledge_counts,
                    'quality_distribution': quality_distribution,
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


class KnowledgeValidator:
    """Validates and scores knowledge quality."""
    
    def __init__(self):
        self.quality_criteria = {
            'completeness': {
                'description_length': 20,    # Minimum characters
                'has_rationale': True,
                'has_context': True,
                'has_tags': True
            },
            'clarity': {
                'readability_threshold': 0.6,  # Readability score
                'has_examples': False,          # Optional
                'clear_terminology': True
            },
            'relevance': {
                'confidence_threshold': 0.5,
                'recent_threshold_days': 365,  # Consider decisions from last year as recent
                'impact_levels': ['medium', 'high', 'critical']
            },
            'uniqueness': {
                'similarity_threshold': 0.8    # Avoid near-duplicates
            }
        }
        
        logger.info("KnowledgeValidator initialized")
    
    def validate_decision(self, decision: DecisionRecord) -> Dict[str, Any]:
        """Validate a decision record and return quality assessment."""
        validation_result = {
            'decision_id': decision.id,
            'overall_score': 0.0,
            'criteria_scores': {},
            'issues': [],
            'recommendations': [],
            'is_valid': True
        }
        
        # Check completeness
        completeness_score, completeness_issues = self._check_completeness(decision)
        validation_result['criteria_scores']['completeness'] = completeness_score
        validation_result['issues'].extend(completeness_issues)
        
        # Check clarity
        clarity_score, clarity_issues = self._check_clarity(decision)
        validation_result['criteria_scores']['clarity'] = clarity_score
        validation_result['issues'].extend(clarity_issues)
        
        # Check relevance
        relevance_score, relevance_issues = self._check_relevance(decision)
        validation_result['criteria_scores']['relevance'] = relevance_score
        validation_result['issues'].extend(relevance_issues)
        
        # Calculate overall score
        scores = validation_result['criteria_scores'].values()
        validation_result['overall_score'] = sum(scores) / len(scores) if scores else 0.0
        
        # Generate recommendations
        validation_result['recommendations'] = self._generate_recommendations(validation_result)
        
        # Determine if valid (threshold: 0.6)
        validation_result['is_valid'] = validation_result['overall_score'] >= 0.6
        
        return validation_result
    
    def validate_knowledge(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted knowledge."""
        validation_result = {
            'knowledge_id': knowledge['id'],
            'overall_score': knowledge.get('quality_score', 0.0),
            'criteria_scores': {},
            'issues': [],
            'recommendations': [],
            'is_valid': True
        }
        
        # Check knowledge-specific criteria
        if not knowledge.get('key_concepts'):
            validation_result['issues'].append('No key concepts extracted')
            validation_result['criteria_scores']['concept_extraction'] = 0.0
        else:
            validation_result['criteria_scores']['concept_extraction'] = 1.0
        
        if not knowledge.get('applicability', {}).get('contexts'):
            validation_result['issues'].append('No applicability contexts defined')
            validation_result['criteria_scores']['applicability'] = 0.5
        else:
            validation_result['criteria_scores']['applicability'] = 1.0
        
        # Use existing quality score as base
        base_score = knowledge.get('quality_score', 0.5)
        additional_scores = list(validation_result['criteria_scores'].values())
        
        if additional_scores:
            validation_result['overall_score'] = (base_score + sum(additional_scores)) / (1 + len(additional_scores))
        
        validation_result['is_valid'] = validation_result['overall_score'] >= 0.6
        
        return validation_result
    
    def _check_completeness(self, decision: DecisionRecord) -> Tuple[float, List[str]]:
        """Check decision completeness."""
        score = 0.0
        issues = []
        
        criteria = self.quality_criteria['completeness']
        
        # Check description length
        if len(decision.description) >= criteria['description_length']:
            score += 0.3
        else:
            issues.append(f"Description too short (minimum {criteria['description_length']} characters)")
        
        # Check rationale
        if decision.rationale and len(decision.rationale) > 5:
            score += 0.3
        else:
            issues.append("Missing or insufficient rationale")
        
        # Check context
        if decision.context and len(decision.context) > 0:
            score += 0.2
        else:
            issues.append("Missing context information")
        
        # Check tags
        if decision.tags and len(decision.tags) > 0:
            score += 0.2
        else:
            issues.append("Missing tags for categorization")
        
        return min(score, 1.0), issues
    
    def _check_clarity(self, decision: DecisionRecord) -> Tuple[float, List[str]]:
        """Check decision clarity."""
        score = 0.7  # Base score for having some content
        issues = []
        
        # Check for clear decision indicators
        clear_indicators = ['decided', 'chose', 'selected', 'implemented', 'adopted']
        if any(indicator in decision.description.lower() for indicator in clear_indicators):
            score += 0.2
        else:
            issues.append("Decision statement could be clearer")
        
        # Check for technical jargon balance
        words = decision.description.split()
        if len(words) > 10:  # Only check longer descriptions
            tech_words = sum(1 for word in words if word[0].isupper() and len(word) > 3)
            if tech_words / len(words) > 0.3:
                issues.append("High technical jargon ratio - consider adding explanations")
                score -= 0.1
        
        return min(score, 1.0), issues
    
    def _check_relevance(self, decision: DecisionRecord) -> Tuple[float, List[str]]:
        """Check decision relevance."""
        score = 0.0
        issues = []
        
        criteria = self.quality_criteria['relevance']
        
        # Check confidence
        if decision.confidence >= criteria['confidence_threshold']:
            score += 0.4
        else:
            issues.append(f"Low confidence score ({decision.confidence:.2f})")
        
        # Check recency
        days_old = (datetime.now() - decision.timestamp).days
        if days_old <= criteria['recent_threshold_days']:
            score += 0.3
        else:
            score += 0.1  # Still some value for older decisions
        
        # Check impact level
        if decision.impact_level in criteria['impact_levels']:
            score += 0.3
        else:
            score += 0.1  # Low impact still has some value
        
        return min(score, 1.0), issues
    
    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving decision quality."""
        recommendations = []
        
        if validation_result['criteria_scores'].get('completeness', 1.0) < 0.8:
            recommendations.append("Add more detailed rationale and context")
        
        if validation_result['criteria_scores'].get('clarity', 1.0) < 0.8:
            recommendations.append("Use clearer decision language and reduce technical jargon")
        
        if validation_result['criteria_scores'].get('relevance', 1.0) < 0.8:
            recommendations.append("Ensure decision has clear impact and current relevance")
        
        if validation_result['overall_score'] < 0.6:
            recommendations.append("Consider capturing more context and detail for this decision")
        
        return recommendations


class KnowledgeCaptureSystem:
    """Main orchestrator for the knowledge capture system."""
    
    def __init__(self, db_path: str = None):
        self.capture_engine = DecisionCaptureEngine()
        self.extractor = KnowledgeExtractor()
        self.integrator = KnowledgeBaseIntegrator(db_path)
        self.validator = KnowledgeValidator()
        
        # Statistics
        self.stats = {
            'decisions_captured': 0,
            'knowledge_extracted': 0,
            'validation_failures': 0,
            'last_run': None
        }
        
        logger.info("KnowledgeCaptureSystem initialized")
    
    def capture_from_codebase(self, project_path: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Capture knowledge from entire codebase."""
        if file_patterns is None:
            file_patterns = ['*.py', '*.js', '*.md', '*.rst']
        
        project_path = Path(project_path)
        captured_decisions = []
        
        # Find relevant files
        relevant_files = []
        for pattern in file_patterns:
            relevant_files.extend(project_path.rglob(pattern))
        
        logger.info(f"Analyzing {len(relevant_files)} files for decisions")
        
        # Process each file
        for file_path in relevant_files:
            try:
                decisions = self.capture_engine.capture_from_code(str(file_path))
                captured_decisions.extend(decisions)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        # Store and extract knowledge
        results = self._process_decisions(captured_decisions)
        
        self.stats['last_run'] = datetime.now().isoformat()
        
        return {
            'decisions_found': len(captured_decisions),
            'decisions_stored': results['stored_decisions'],
            'knowledge_extracted': results['extracted_knowledge'],
            'validation_summary': results['validation_summary'],
            'statistics': self.integrator.get_statistics()
        }
    
    def capture_from_session_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Capture knowledge from session data."""
        try:
            decisions = self.capture_engine.capture_from_session(session_data)
            results = self._process_decisions(decisions)
            
            return {
                'decisions_captured': len(decisions),
                'decisions_stored': results['stored_decisions'],
                'knowledge_extracted': results['extracted_knowledge'],
                'validation_summary': results['validation_summary']
            }
        except sqlite3.OperationalError as e:
            # Handle database-specific errors
            logger.error(f"Database error in knowledge capture: {e}")
            raise OSError(f"Database access error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in knowledge capture: {e}")
            raise
    
    def search_knowledge(self, query: str, knowledge_type: str = None) -> Dict[str, Any]:
        """Search the knowledge base."""
        # Search decisions
        decisions = self.integrator.search_decisions(query)
        
        # Get related knowledge
        knowledge_items = []
        if knowledge_type:
            knowledge_items = self.integrator.get_knowledge_by_type(knowledge_type)
        else:
            # Get knowledge from found decisions
            for decision in decisions:
                related_knowledge = self.integrator.get_knowledge_by_type('all')  # Would need to modify this
                knowledge_items.extend([k for k in related_knowledge if k['source_decision'] == decision.id])
        
        return {
            'query': query,
            'decisions_found': len(decisions),
            'knowledge_items_found': len(knowledge_items),
            'decisions': [decision.to_dict() for decision in decisions],
            'knowledge': knowledge_items
        }
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights from the knowledge base."""
        stats = self.integrator.get_statistics()
        
        # Generate insights
        insights = {
            'knowledge_base_health': self._assess_knowledge_base_health(stats),
            'top_decision_types': self._get_top_categories(stats.get('decisions_by_type', {})),
            'knowledge_quality_trends': self._analyze_quality_trends(stats),
            'recommendations': self._generate_system_recommendations(stats),
            'coverage_analysis': self._analyze_coverage()
        }
        
        return {
            'statistics': stats,
            'insights': insights,
            'generated_at': datetime.now().isoformat()
        }
    
    def _process_decisions(self, decisions: List[DecisionRecord]) -> Dict[str, Any]:
        """Process a list of decisions through the full pipeline."""
        stored_decisions = 0
        extracted_knowledge = 0
        validation_results = []
        
        for decision in decisions:
            # Validate decision
            validation = self.validator.validate_decision(decision)
            validation_results.append(validation)
            
            if validation['is_valid']:
                # Store decision
                if self.integrator.store_decision(decision):
                    stored_decisions += 1
                    
                    # Extract and store knowledge
                    knowledge = self.extractor.extract_knowledge(decision)
                    knowledge_validation = self.validator.validate_knowledge(knowledge)
                    
                    if knowledge_validation['is_valid']:
                        if self.integrator.store_knowledge(knowledge):
                            extracted_knowledge += 1
            else:
                self.stats['validation_failures'] += 1
        
        # Update stats
        self.stats['decisions_captured'] += len(decisions)
        self.stats['knowledge_extracted'] += extracted_knowledge
        
        return {
            'stored_decisions': stored_decisions,
            'extracted_knowledge': extracted_knowledge,
            'validation_summary': {
                'total_validated': len(validation_results),
                'passed_validation': sum(1 for v in validation_results if v['is_valid']),
                'failed_validation': sum(1 for v in validation_results if not v['is_valid']),
                'average_score': sum(v['overall_score'] for v in validation_results) / len(validation_results) if validation_results else 0
            }
        }
    
    def _assess_knowledge_base_health(self, stats: Dict[str, Any]) -> str:
        """Assess overall health of knowledge base."""
        total_items = stats.get('total_decisions', 0) + stats.get('total_knowledge', 0)
        
        if total_items < 10:
            return 'building'
        elif total_items < 50:
            return 'growing'
        elif total_items < 200:
            return 'healthy'
        else:
            return 'mature'
    
    def _get_top_categories(self, category_counts: Dict[str, int], top_n: int = 3) -> List[Tuple[str, int]]:
        """Get top N categories by count."""
        return sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def _analyze_quality_trends(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quality trends in the knowledge base."""
        quality_dist = stats.get('quality_distribution', {})
        total_items = sum(quality_dist.values())
        
        if total_items == 0:
            return {'status': 'no_data'}
        
        high_quality_pct = (quality_dist.get('high', 0) / total_items) * 100
        
        return {
            'high_quality_percentage': high_quality_pct,
            'quality_status': 'excellent' if high_quality_pct > 70 else 'good' if high_quality_pct > 50 else 'needs_improvement'
        }
    
    def _generate_system_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving the knowledge capture system."""
        recommendations = []
        
        total_decisions = stats.get('total_decisions', 0)
        total_knowledge = stats.get('total_knowledge', 0)
        
        if total_decisions < 10:
            recommendations.append("Increase decision capture by analyzing more project files and session data")
        
        if total_knowledge < total_decisions * 0.8:
            recommendations.append("Improve knowledge extraction rate from captured decisions")
        
        quality_dist = stats.get('quality_distribution', {})
        if quality_dist.get('low', 0) > quality_dist.get('high', 0):
            recommendations.append("Focus on improving knowledge quality through better validation and capture techniques")
        
        return recommendations
    
    def _analyze_coverage(self) -> Dict[str, Any]:
        """Analyze knowledge coverage across different areas."""
        # This would analyze the spread of knowledge across different domains
        return {
            'domain_coverage': 'balanced',  # Placeholder
            'temporal_coverage': 'recent',   # Placeholder
            'completeness_score': 0.75      # Placeholder
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize the knowledge capture system
    kcs = KnowledgeCaptureSystem()
    
    # Example: Capture from current project
    print("🚀 Starting Knowledge Capture System Test")
    
    # Test with sample decision
    sample_decision = DecisionRecord(
        id="test_001",
        timestamp=datetime.now(),
        decision_type="technical",
        description="Decided to use SQLite for knowledge storage because it provides full-text search capabilities and doesn't require external dependencies",
        rationale="SQLite offers FTS5 for full-text search while being lightweight and portable",
        context={"project": "workflow_automation", "phase": "3"},
        impact_level="medium",
        tags=["database", "architecture", "tech:sqlite"],
        source="design",
        confidence=0.8,
        related_files=["knowledge_capture.py"]
    )
    
    # Process the sample decision
    validation = kcs.validator.validate_decision(sample_decision)
    print(f"✅ Validation result: {validation['overall_score']:.2f} (Valid: {validation['is_valid']})")
    
    if validation['is_valid']:
        # Store decision
        stored = kcs.integrator.store_decision(sample_decision)
        print(f"📁 Decision stored: {stored}")
        
        # Extract knowledge
        knowledge = kcs.extractor.extract_knowledge(sample_decision)
        knowledge_stored = kcs.integrator.store_knowledge(knowledge)
        print(f"🧠 Knowledge extracted and stored: {knowledge_stored}")
        
        # Search test
        search_results = kcs.search_knowledge("SQLite database")
        print(f"🔍 Search results: {search_results['decisions_found']} decisions found")
        
        # Get insights
        insights = kcs.get_insights()
        print(f"📊 Knowledge base health: {insights['insights']['knowledge_base_health']}")
    
    print("✅ Knowledge Capture System test completed")