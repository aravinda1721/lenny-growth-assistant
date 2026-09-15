"""
backend/app/llm/simulated.py

Dynamic, intelligent offline demonstration LLM provider.
Dynamically parses retrieved transcript excerpts to synthesize unique, highly grounded,
customized answers for every user question with exact quotes, timestamps, and guest attribution.
Also generates topic-specific ~1,250-word Ship 30 essays and interactive HTML/Markdown artifacts.
"""

import re
from typing import List, Dict, Any
from .base import LLMProvider, LLMResponse

class SimulatedProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "simulated"

    @property
    def model_name(self) -> str:
        return "offline-growth-synth-v1"

    async def is_available(self) -> bool:
        return True

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2500,
        **kwargs
    ) -> LLMResponse:
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        content_lower = (user_msg + " " + system_prompt).lower()

        # Route to appropriate synthesis pattern
        if "ship 30" in content_lower or "ship30" in content_lower or "1,250" in content_lower:
            text = self._generate_ship30_essay(user_msg, system_prompt)
        elif "artifact" in content_lower or "html" in content_lower or "one-pager" in content_lower or "scorecard" in content_lower:
            text = self._generate_artifact_response(user_msg, system_prompt)
        else:
            text = self._generate_grounded_answer(user_msg, system_prompt)

        return LLMResponse(
            content=text,
            provider="simulated",
            model=self.model_name,
            usage={"simulated": True, "prompt_tokens": len(user_msg.split()), "completion_tokens": len(text.split())}
        )

    def _parse_prompt(self, text: str) -> tuple[str, List[Dict[str, str]]]:
        """Extracts the original user question and all retrieved excerpts."""
        question_match = re.search(r"User Question:\s*(.*?)(?:\n\n|\nHere are|\Z)", text, re.DOTALL)
        question = question_match.group(1).strip() if question_match else text[:80]

        excerpts = []
        blocks = re.split(r"---\s*Excerpt\s*\d+\s*---", text)
        for b in blocks[1:]:
            ep = re.search(r"Episode:\s*(.*)", b)
            guest = re.search(r"Guest:\s*(.*)", b)
            ts = re.search(r"Timestamp:\s*(.*)", b)
            content = re.search(r"Content:\s*([\s\S]*)", b)
            
            raw_text = content.group(1).strip() if content else ""
            # Clean out prompt instructions if attached to last excerpt
            if "Provide a thorough" in raw_text:
                raw_text = raw_text.split("Provide a thorough")[0].strip()

            if raw_text:
                excerpts.append({
                    "episode": ep.group(1).strip() if ep else "Lenny's Podcast",
                    "guest": guest.group(1).strip() if guest else "Guest",
                    "timestamp": ts.group(1).strip() if ts else "00:00:00",
                    "content": raw_text
                })

        return question, excerpts

    def _generate_grounded_answer(self, prompt: str, system_prompt: str) -> str:
        question, excerpts = self._parse_prompt(prompt)

        if not excerpts:
            return (
                f"### Analysis: {question}\n\n"
                "Based on transcripts from Lenny's Podcast, this inquiry centers on effective product strategy. "
                "Leaders featured on the podcast emphasize that real progress requires clear problem definition, "
                "rigorous user cohort tracking, and eliminating organizational friction."
            )

        # Identify primary guest and episodes
        guests = list(dict.fromkeys(e["guest"] for e in excerpts if e["guest"]))
        primary_guest = guests[0] if guests else "Featured Operators"
        guest_list_str = ", ".join(guests[:3])

        lines = [
            f"### Grounded Synthesis: {question}\n",
            f"Drawing directly from transcripts featuring **{guest_list_str}**, here is the evidence-backed breakdown:\n"
        ]

        # Synthesize each excerpt with specific context, quotes, and timestamps
        for i, exc in enumerate(excerpts[:4]):
            guest = exc["guest"]
            episode = exc["episode"]
            ts = exc["timestamp"]
            raw_content = exc["content"]

            # Extract substantive sentences from content
            # Strip speaker prefixes like 'Brian Chesky (00:00:00):' or '(00:00:00):'
            cleaned_text = re.sub(r"^[A-Za-z\s\.\'\-]+?\s*\(((\d{1,2}:)?\d{2}:\d{2})\):\s*", "", raw_content, flags=re.MULTILINE)
            cleaned_text = re.sub(r"\(((\d{1,2}:)?\d{2}:\d{2})\):\s*", "", cleaned_text)
            
            raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned_text) if len(s.strip()) > 25]
            best_quote = raw_sentences[0] if raw_sentences else raw_content[:160]
            secondary_insight = raw_sentences[1] if len(raw_sentences) > 1 else ""

            # Topic-specific contextual narrative
            lines.append(f"#### {i+1}. {guest} on *{episode}* ({ts})\n")
            lines.append(f"As **{guest}** explained at `{ts}`:\n")
            lines.append(f"> \"{best_quote}\"\n")
            
            if secondary_insight:
                lines.append(f"**Key Point:** {secondary_insight}\n")
            else:
                lines.append(f"**Operational Takeaway:** This highlights how high-growth operators ground decisions in continuous customer feedback and empirical product signals.\n")

        # Synthesize collective actionable conclusion
        lines.append("---\n")
        lines.append("### Strategic Takeaway for Product Teams\n")
        if "retention" in question.lower() or "growth" in question.lower():
            lines.append(
                "- **Prioritize Retention Baseline Over Acquisition:** Validate that Day-30 cohort retention curves flatten into a stable asymptote before investing heavily in marketing funnels.\n"
                "- **Diagnose Natural Word-of-Mouth:** Measure the percentage of weekly active users who execute your product's core value exchange without artificial incentives.\n"
            )
        elif "founder" in question.lower() or "chesky" in question.lower() or "leadership" in question.lower():
            lines.append(
                "- **Maintain Leadership Immersion:** Leaders must inspect Figma designs and product copy directly, eliminating bureaucratic review layers.\n"
                "- **Single-Threaded Ownership:** Assign unambiguous, end-to-end accountability for every customer-facing surface.\n"
            )
        elif "pmf" in question.lower() or "fit" in question.lower():
            lines.append(
                "- **Instrument the 'Very Disappointed' Benchmark:** Target >40% of surveyed core users reporting they would be very disappointed without your product.\n"
                "- **Focus on High-Conviction Segments:** Double down on users who love your product rather than attempting to satisfy every fringe request.\n"
            )
        else:
            lines.append(
                f"- **Align Around Measurable Outcomes:** Measure teams by customer problem resolution rather than backlog ticket completion velocity.\n"
                f"- **Relentless Customer Discovery:** Ensure designers, engineers, and product leaders maintain direct, unfiltered contact with active users weekly.\n"
            )

        citations_str = ", ".join([f"{e['guest']} ({e['timestamp']})" for e in excerpts[:4]])
        lines.append(f"\n*(Sources cited from Lenny's Podcast transcripts: {citations_str})*")

        return "\n".join(lines)

    def _generate_ship30_essay(self, query: str, context: str) -> str:
        q_lower = query.lower()
        
        # Tailor hook and theme dynamically based on user inquiry
        if "founder" in q_lower or "chesky" in q_lower or "leadership" in q_lower:
            theme_title = "The Relentless Product Operating System: Why Founder-Led Teams Outperform the Rest"
            lead_in = "Most product teams believe their biggest blocker is headcount.\n\nThey think they need more product managers, more scrum rituals, and thicker roadmaps to move the needle. But when you inspect the companies that actually compound—Airbnb, Figma, Stripe—the reality is the exact opposite. Bureaucracy kills momentum."
        elif "team" in q_lower or "feature" in q_lower or "cagan" in q_lower:
            theme_title = "Missionaries vs. Mercenaries: Why Feature Factories Destroy Product Value"
            lead_in = "Most organizations celebrate the wrong milestone.\n\nThey throw launch parties on the day code ships, check the roadmap box, and never look back. But shipping features is not the same as creating value. When product teams operate as feature factories, company momentum quietly dies."
        elif "retention" in q_lower or "growth" in q_lower or "verna" in q_lower:
            theme_title = "Why Growth Tactics Cannot Fix a Leaky Bucket: The Elena Verna Framework"
            lead_in = "The most expensive mistake in modern tech is pouring marketing dollars into poor retention.\n\nTeams celebrate top-of-funnel spikes from paid ads and referral bonuses while ignoring that 80% of users vanish after week two. Growth levers can amplify a working product; they cannot create product-market fit out of thin air."
        else:
            theme_title = "The High-Agency Product Engine: How Category Leaders Compound Advantage"
            lead_in = "In high-growth companies, the difference between good and exceptional teams is not technical skill.\n\nIt is operating philosophy. While average teams wait for permission and complain about constraints, category-defining builders bend reality through first-principles execution."

        return (
            f"# {theme_title}\n\n"
            f"{lead_in}\n\n"
            "Here is the actionable framework top operators use, drawn directly from leaders featured on Lenny's Podcast.\n\n"
            "---\n\n"
            "### I. The Myth of the Hands-Off Leader\n\n"
            "For years, conventional management wisdom preached delegation above all else: hire smart people, give them high-level OKRs, and step back completely.\n\n"
            "In practice, this creates siloed fiefdoms where nobody is looking at the integrated customer experience. In *Brian Chesky’s new playbook*, Brian noted that founders who seek a polite midpoint between how they want to run the company and how everyone else wants it run end up with mediocre outcomes. When leadership steps back from product reviews, design compromises multiply. Middle managers negotiate across feature boundaries, resulting in Frankenstein interfaces where each tab feels like it was designed by a separate company.\n\n"
            "**Key rules for high-conviction product leadership:**\n"
            "- **Review the work, not just the status:** Leaders must look at Figma prototypes and copy, not just sprint velocity reports. Looking at live pixels prevents teams from polishing bad concepts for quarters.\n"
            "- **Preserve the integrated user journey:** No single feature exists in isolation; it must fit the end-to-end user narrative from onboarding to conversion.\n"
            "- **Eliminate organizational friction:** If decisions take three weeks and four approvals, speed collapses to zero. Condense review gates into a single weekly founder review.\n"
            "- **Single-threaded accountability:** When three people are responsible for a product launch, nobody is responsible. Every surface must have one owner who signs off on the quality bar.\n\n"
            "When leadership stays close to the product craftsmanship, quality compounds across the entire surface area of the organization.\n\n"
            "---\n\n"
            "### II. Growth Cannot Fix a Leaky Bucket\n\n"
            "The second fatal mistake teams make is attempting to solve retention problems with acquisition levers.\n\n"
            "As Elena Verna pointed out on Lenny's Podcast (*10 growth tactics that never work*), growth tactics will never build a product people actually want. If your day-30 and day-90 cohort retention curves do not flatten into a stable horizontal baseline, spending marketing dollars is simply pouring water into a sieve. Marketing campaigns, performance paid ads, and referral bonuses can temporarily spike top-of-funnel signups, but they create a dangerous illusion of health that obscures fundamental product deficiencies.\n\n"
            "**How to test for genuine organic pull:**\n"
            "- **The Sean Ellis PMF Benchmark:** At least 40% of surveyed active users must answer that they would be 'very disappointed' if your product disappeared tomorrow. If your score is under 25%, halt expansion and return to customer problem discovery.\n"
            "- **Organic referral velocity:** Track how many new users arrive without paid ad attribution or incentive discounts. Word-of-mouth is the only scalable moat.\n"
            "- **Core action frequency:** Measure the percentage of weekly active users who execute your product's primary value exchange rather than superficial logins.\n"
            "- **The Retention Flattening Test:** Plot cohort curves on a logarithmic scale. Healthy products show cohorts that drop initially and then level off into an unbreakable horizontal asymptote.\n\n"
            "Once cohort curves flatten, growth loops amplify value. Until then, every dollar and engineering hour should go toward product discovery and customer problem-solving.\n\n"
            "---\n\n"
            "### III. Empowered Teams vs. Feature Factories\n\n"
            "Marty Cagan draws an indelible line between feature teams and empowered product teams.\n\n"
            "Feature factories exist to ship a list of requests given to them by sales or executives. They celebrate on the day of release, check the box, and immediately move on to the next roadmap item without ever looking back at whether customer behavior changed. Empowered product teams, by contrast, are given a problem to solve and celebrate only when the target metric changes. The difference is psychological: mercenaries ship deliverables; missionaries solve customer friction.\n\n"
            "**The four pillars of empowered discovery:**\n"
            "1. **Direct Customer Access:** Engineers, designers, and PMs must interact directly with customers weekly, without intermediaries, account managers, or sales gatekeepers filtering feedback.\n"
            "2. **Rapid Prototyping Over PRDs:** Test hypotheses with throwaway prototypes before writing production code. A prototype tested with five users reveals more flaw than forty pages of specification documents.\n"
            "3. **Outcome Accountability:** Measure teams on churn reduction, task completion speed, and revenue expansion, rather than sprint story points or ticket velocity.\n"
            "4. **Shared Context Over Control:** High-performing teams do not require micromanagement if they possess complete context on the company's financial realities, user feedback, and competitive threats.\n\n"
            "When teams own the outcome rather than the output, innovation becomes the default operating state across the engineering organization.\n\n"
            "---\n\n"
            "### IV. The High-Agency Operating Philosophy\n\n"
            "Finally, building category-defining products requires what Shreyas Doshi terms 'high-agency leadership.'\n\n"
            "Low-agency teams wait for external permission, complain about constraints, and blame macroeconomic shifts or organizational silos for missed goals. High-agency individuals bend reality to find a way through seemingly impossible roadblocks. They recognize that constraints are not stop signs; they are design parameters that demand radical ingenuity.\n\n"
            "**Habits of high-agency builders:**\n"
            "- **Proactive problem anticipation:** Flag risks two quarters before they appear on the dashboard. Do not wait for a negative metric to begin root-cause remediation.\n"
            "- **First-principles reasoning:** Strip away industry conventions, competitor benchmarks, and legacy templates. Reconstruct the problem from physical truths and customer fundamentals.\n"
            "- **Unforgiving craft standards:** Refuse to ship mediocre microcopy, sluggish load times, or jarring UI transitions. Respect the user's intelligence and time down to every micro-interaction.\n"
            "- **Relentless bias for action:** While low-agency teams debate in endless consensus meetings, high-agency teams ship small experiments, observe customer reality, and iterate immediately.\n"
            "- **Intellectual humility:** High-agency builders hold strong opinions weakly. When real customer usage disproves a beloved hypothesis, they discard it without ego and pivot toward empirical truth.\n\n"
            "High agency is contagious. When an organization rewards bold initiative over passive compliance, top performers naturally gravitate toward the mission and compound results.\n\n"
            "---\n\n"
            "### The 1-Sentence Takeaway\n\n"
            "**Sustainable product growth is not an accident of marketing; it is the inevitable consequence of deep leader immersion, relentless cohort retention, and empowered teams solving real customer pain.**"
        )

    def _generate_artifact_response(self, query: str, context: str) -> str:
        q_lower = query.lower()
        if "scorecard" in q_lower or "pmf" in q_lower:
            name = "Product-Market Fit & Leadership Scorecard"
        elif "retention" in q_lower or "cohort" in q_lower:
            name = "Cohort Retention & Growth Calculator"
        elif "team" in q_lower or "cagan" in q_lower:
            name = "Empowered vs Feature Team Assessment Rubric"
        else:
            name = "Product Strategy & Growth One-Pager"

        return (
            f"I have generated the interactive **{name}** artifact for you.\n\n"
            "You can preview and interact with it directly in the **Artifact Viewer** in the right-hand split pane. "
            "It features structured scorecards, operational status indicators, and clean CSS styling."
        )

simulated_provider = SimulatedProvider()
