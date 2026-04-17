from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import Post, Category
from django.utils.text import slugify
import random
from django.core.files.base import ContentFile
import os
from django.conf import settings
import requests
from io import BytesIO

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates 6 sample blog posts'
    
    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Username of the post author')
    
    def handle(self, *args, **options):
        # Get or create categories
        categories = self._ensure_categories()
        
        # Get or create user
        username = options.get('user')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with username "{username}" does not exist'))
                return
        else:
            # Get the first superuser or staff user
            user = User.objects.filter(is_superuser=True).first() or User.objects.filter(is_staff=True).first()
            if not user:
                user = User.objects.first()
                if not user:
                    self.stdout.write(self.style.ERROR('No users found in the database'))
                    return
        
        # Blog post content
        posts = [
            {
                'title': '10 Essential SEO Techniques for 2025',
                'excerpt': 'Master these crucial SEO techniques to stay ahead of the competition in 2025 and beyond.',
                'content': """
<p>Search Engine Optimization continues to evolve rapidly as search algorithms become more sophisticated. To stay competitive in 2025, websites need to implement these essential techniques:</p>

<h2>1. AI-Powered Content Optimization</h2>
<p>With advances in AI, content optimization now goes beyond keywords. Use AI tools to analyze search intent, predict user questions, and create comprehensive content that addresses all aspects of a topic.</p>

<h2>2. User Experience Signals</h2>
<p>Google's algorithm heavily weighs user experience metrics like Core Web Vitals, mobile-friendliness, and page interactivity. Focus on creating fast, responsive, and engaging pages.</p>

<h2>3. E-A-T Content Strategy</h2>
<p>Expertise, Authoritativeness, and Trustworthiness (E-A-T) continue to be crucial ranking factors. Develop content that demonstrates deep expertise and build your site's authority through quality backlinks and proper citations.</p>

<h2>4. Voice Search Optimization</h2>
<p>With voice assistants becoming ubiquitous, optimizing for conversational queries is essential. Focus on natural language patterns and question-based content.</p>

<h2>5. Video Content Integration</h2>
<p>Video has become a dominant content format. Integrating optimized video content with proper transcripts and structured data can significantly boost SEO performance.</p>

<h2>6. Semantic Search Understanding</h2>
<p>Search engines now understand context and relationships between topics. Build comprehensive topic clusters that cover related concepts and establish your site as an authority.</p>

<h2>7. Privacy-Focused Analytics</h2>
<p>As third-party cookies phase out, implement first-party data collection and privacy-friendly analytics to continue understanding user behavior while respecting privacy regulations.</p>

<h2>8. Local SEO Enhancement</h2>
<p>For businesses with physical locations, local SEO remains critical. Optimize Google Business Profiles, gather reviews, and create location-specific content.</p>

<h2>9. Technical SEO Automation</h2>
<p>Implement automated monitoring for technical SEO issues such as broken links, crawl errors, and site performance issues to address problems before they impact rankings.</p>

<h2>10. Multimodal Search Preparation</h2>
<p>Prepare for multimodal search capabilities that combine text, voice, images, and video queries. Ensure your content is accessible across multiple formats and query types.</p>

<p>By implementing these techniques, you'll be well-positioned to maintain and improve your search visibility throughout 2025 and beyond.</p>
                """,
                'category': 'SEO Techniques'
            },
            {
                'title': 'How AI is Transforming Content Creation',
                'excerpt': 'Discover how artificial intelligence is revolutionizing content marketing and what this means for your digital strategy.',
                'content': """
<p>Artificial intelligence is no longer a futuristic concept—it's actively reshaping how we create, distribute, and optimize content. Here's how AI is transforming the content creation landscape:</p>

<h2>The Rise of AI Content Tools</h2>
<p>Content creation platforms powered by machine learning algorithms can now generate everything from blog posts and social media updates to complex technical documentation. These tools analyze vast datasets of existing content to understand patterns, style, and structure, then apply these insights to create new material that's increasingly difficult to distinguish from human-written content.</p>

<h2>Personalization at Scale</h2>
<p>AI enables unprecedented content personalization by analyzing user behavior and preferences. Content can now be dynamically tailored to individual users based on their browsing history, purchase patterns, and demographic information. This level of personalization was previously impossible to achieve manually, especially for websites with thousands or millions of visitors.</p>

<h2>Enhanced Research Capabilities</h2>
<p>AI-powered research tools can rapidly analyze millions of articles, reports, and data points to identify trends, gather statistics, and provide comprehensive information on any topic. This drastically reduces the time content creators spend on research and increases the accuracy and depth of the resulting content.</p>

<h2>Multilingual Content Production</h2>
<p>Neural machine translation has significantly improved the quality of automated translations. AI can now create multilingual content that preserves the nuance and context of the original while adapting to cultural differences in different markets—all without requiring multiple human translators.</p>

<h2>Content Optimization in Real-Time</h2>
<p>AI tools can continuously analyze content performance and suggest improvements in real-time. These adjustments might include tweaking headlines, reorganizing sections for better readability, or updating information to reflect current events and trends.</p>

<h2>The Human Element Remains Essential</h2>
<p>Despite these advances, human oversight remains critical. AI excels at handling routine content tasks but still struggles with creative innovation, emotional intelligence, and the nuanced understanding of human experiences. The most effective content strategies combine AI's efficiency with human creativity and strategic direction.</p>

<p>As we move forward, organizations that successfully integrate AI into their content creation process while maintaining a distinct brand voice and human touch will gain significant advantages in the increasingly competitive digital landscape.</p>
                """,
                'category': 'Content Marketing'
            },
            {
                'title': 'Mobile-First Indexing: What You Need to Know',
                'excerpt': 'Mobile-first indexing has changed how Google ranks websites. Learn what this means for your site and how to optimize accordingly.',
                'content': """
<p>Mobile-first indexing has fundamentally changed how Google evaluates and ranks websites. This approach prioritizes the mobile version of your site for indexing and ranking, reflecting the reality that most users now access the web via smartphones and tablets. Here's what you need to understand to stay competitive:</p>

<h2>What is Mobile-First Indexing?</h2>
<p>Mobile-first indexing means Google predominantly uses the mobile version of a website's content for indexing and ranking. Prior to this shift, Google's crawling, indexing, and ranking systems used the desktop version of a site's content, which could create problems when the mobile page had less content or performed differently than the desktop version.</p>

<h2>Why Mobile-First Matters</h2>
<p>With over 60% of Google searches now conducted on mobile devices, prioritizing mobile experience is not optional. Sites that offer poor mobile experiences face significant penalties in search rankings, regardless of how well their desktop versions perform. Google has made it clear that mobile usability is a critical ranking factor.</p>

<h2>Key Optimization Strategies</h2>

<h3>Responsive Design Implementation</h3>
<p>Implement responsive web design that automatically adapts your site's layout to any screen size. This approach is Google's recommended method for mobile optimization as it ensures content consistency across devices while simplifying maintenance.</p>

<h3>Content Parity</h3>
<p>Ensure your mobile site contains the same content as your desktop version. Hidden content, reduced text, or missing images on mobile can negatively impact rankings. If you must reduce content for mobile, focus on presentation rather than removing valuable information.</p>

<h3>Page Speed Optimization</h3>
<p>Mobile users expect fast-loading pages, and Google's algorithms favor sites that deliver. Compress images, leverage browser caching, minimize code, and consider implementing AMP (Accelerated Mobile Pages) for critical content.</p>

<h3>Improved Navigation</h3>
<p>Mobile navigation should be intuitive and touch-friendly. Implement hamburger menus, ensure buttons are large enough to tap accurately, and keep important actions within easy reach of users' thumbs.</p>

<h3>Technical Considerations</h3>
<p>Avoid mobile-specific errors like blocked JavaScript, CSS, or image files. Ensure your robots.txt doesn't block Googlebot from crawling critical resources needed to render mobile pages properly.</p>

<h3>Metadata Consistency</h3>
<p>Maintain equivalent title tags, meta descriptions, and structured data across mobile and desktop versions. These elements should accurately represent page content regardless of the device used to access it.</p>

<h2>Testing Your Mobile Optimization</h2>
<p>Use Google's Mobile-Friendly Test, Mobile Usability Report in Search Console, and PageSpeed Insights to evaluate your site's mobile performance. Address any issues these tools identify to improve your standing in mobile search results.</p>

<p>As mobile usage continues to grow, prioritizing mobile optimization is not just about maintaining search rankings—it's about providing the best possible experience for the majority of your users. By embracing mobile-first principles, you position your site for success in an increasingly mobile-dominated digital landscape.</p>
                """,
                'category': 'Technical SEO'
            },
            {
                'title': '7 Effective Link Building Strategies for 2025',
                'excerpt': 'Quality backlinks remain crucial for SEO success. Discover 7 effective and ethical link building strategies for the coming year.',
                'content': """
<p>Despite constant evolution in search algorithms, quality backlinks remain a cornerstone of effective SEO. However, as search engines become more sophisticated at detecting manipulative tactics, link building strategies must focus on value, relevance, and authenticity. Here are seven effective approaches for building quality backlinks in 2025:</p>

<h2>1. Original Research and Data Publication</h2>
<p>Creating original research, surveys, and data analysis provides exceptional link-worthy content. When you publish unique insights backed by data, other websites naturally reference your findings and link to your content as the original source. This strategy not only generates high-quality backlinks but also establishes your brand as an industry authority.</p>

<p>Implementation tip: Identify information gaps in your industry and design research projects that address unanswered questions or provide updated statistics on evolving trends.</p>

<h2>2. Strategic Guest Posting</h2>
<p>While mass guest posting for links has been devalued, strategic contributions to reputable publications in your niche remain effective. The key difference is focusing on quality over quantity and ensuring genuine value for the host site's audience.</p>

<p>Implementation tip: Target publications with engaged communities relevant to your expertise. Craft unique content that showcases your knowledge while naturally incorporating references to your relevant resources.</p>

<h2>3. Resource Link Building</h2>
<p>Creating comprehensive resources like guides, templates, calculators, or tools makes your site a natural target for links from related content. When your resource becomes the go-to reference for specific information or functionality, links follow organically.</p>

<p>Implementation tip: Develop evergreen resources that solve common problems in your industry. Then strategically promote these resources to websites and influencers who regularly share similar content with their audiences.</p>

<h2>4. Digital PR and Newsjacking</h2>
<p>Securing media coverage through digital PR campaigns or timely commentary on trending news provides valuable backlink opportunities from authoritative news sites. This approach requires agility and relevant expertise but can yield significant results.</p>

<p>Implementation tip: Develop relationships with journalists covering your industry and monitor trending topics where your brand can offer meaningful insights or unique perspectives.</p>

<h2>5. Broken Link Reclamation</h2>
<p>Identifying broken links on reputable websites provides an opportunity to suggest your content as a replacement. This creates a win-win situation where you gain a quality backlink while helping the site fix broken links that harm user experience.</p>

<p>Implementation tip: Use tools like Ahrefs or Check My Links to identify broken links on authoritative sites in your niche, then reach out with a helpful suggestion that includes your relevant content as a replacement option.</p>

<h2>6. Collaborative Content Creation</h2>
<p>Partnering with complementary brands, industry experts, or influencers to create co-branded content generates natural backlinks through cross-promotion. This approach expands your reach while acquiring links from established domains.</p>

<p>Implementation tip: Identify potential partners whose audience overlaps with yours but isn't directly competitive. Propose collaborative projects like webinars, research studies, or comprehensive guides that benefit both parties.</p>

<h2>7. Community Participation and Brand Mentions</h2>
<p>Active participation in industry forums, expert panels, podcast interviews, and online communities builds relationships that naturally lead to backlinks. Meaningful contributions establish your expertise and increase the likelihood of organic link inclusion.</p>

<p>Implementation tip: Focus on providing value in conversations rather than explicitly seeking links. When your insights help others, attribution through links follows naturally.</p>

<h2>The Future of Link Building</h2>
<p>As search algorithms continue to evolve, link building will increasingly merge with broader brand building efforts. The most sustainable approach focuses on creating link-worthy content and experiences while building genuine relationships within your industry ecosystem.</p>

<p>Remember that effective link building requires patience and consistency. Focus on quality over quantity, and integrate these strategies into your broader digital marketing efforts for maximum impact.</p>
                """,
                'category': 'Link Building'
            },
            {
                'title': 'Understanding Core Web Vitals for Better Rankings',
                'excerpt': 'Core Web Vitals have become essential ranking factors. Learn what they are and how to optimize your site to meet Google\'s standards.',
                'content': """
<p>Core Web Vitals have transformed from optional performance metrics to critical ranking factors that directly impact your website's visibility in search results. Understanding and optimizing these metrics is essential for maintaining and improving your search rankings in today's performance-focused search landscape.</p>

<h2>What Are Core Web Vitals?</h2>
<p>Core Web Vitals are a set of specific factors that Google considers important for overall user experience on web pages. They measure aspects of web usability such as load time, interactivity, and visual stability. The three current Core Web Vitals metrics are:</p>

<h3>1. Largest Contentful Paint (LCP)</h3>
<p>LCP measures loading performance by tracking how long it takes for the largest content element visible in the viewport to render. This could be an image, video, or block of text. For good user experience, LCP should occur within 2.5 seconds of when the page first starts loading.</p>

<h3>2. First Input Delay (FID)</h3>
<p>FID measures interactivity by tracking the time from when a user first interacts with your page (e.g., clicks a link or button) to when the browser is actually able to respond to that interaction. For good user experience, pages should have an FID of less than 100 milliseconds.</p>

<p>Note: Google has announced that in March 2024, FID will be replaced by Interaction to Next Paint (INP), which measures overall responsiveness to all user interactions, not just the first one.</p>

<h3>3. Cumulative Layout Shift (CLS)</h3>
<p>CLS measures visual stability by quantifying how much unexpected layout shift occurs during the entire lifespan of the page. For good user experience, pages should maintain a CLS score of less than 0.1.</p>

<h2>Why Core Web Vitals Matter</h2>
<p>Core Web Vitals have direct implications for your website's performance in search results:</p>

<ul>
  <li>They are confirmed ranking factors in Google's algorithm</li>
  <li>They impact user experience, affecting bounce rates and conversion rates</li>
  <li>They provide measurable metrics for performance optimization</li>
  <li>They influence how quickly and effectively Google indexes your content</li>
</ul>

<h2>How to Optimize for Core Web Vitals</h2>

<h3>Improving LCP</h3>
<p><strong>Server optimization:</strong> Upgrade hosting, implement caching, and use CDNs to improve server response times.</p>
<p><strong>Resource optimization:</strong> Compress and properly format images and videos, eliminate render-blocking resources, and minify CSS and JavaScript.</p>
<p><strong>Prioritize above-the-fold content:</strong> Structure your HTML to load critical content first.</p>

<h3>Improving FID/INP</h3>
<p><strong>Optimize JavaScript execution:</strong> Break up long tasks, optimize event handlers, and defer non-essential JavaScript.</p>
<p><strong>Reduce third-party code impact:</strong> Audit and limit third-party scripts that block the main thread.</p>
<p><strong>Implement browser hints:</strong> Use preload, prefetch, and preconnect to optimize resource loading.</p>

<h3>Improving CLS</h3>
<p><strong>Set explicit dimensions for media:</strong> Always include width and height attributes for images and videos.</p>
<p><strong>Reserve space for dynamic content:</strong> Allocate space for ads, embeds, and iframes that load after the initial page render.</p>
<p><strong>Avoid inserting content above existing content:</strong> Add new content below the viewport when possible.</p>
<p><strong>Use transform animations:</strong> Choose CSS transform properties for animations instead of properties that trigger layout changes.</p>

<h2>Tools for Measuring Core Web Vitals</h2>
<p>Several tools can help you measure and monitor your Core Web Vitals performance:</p>

<ul>
  <li>Google PageSpeed Insights: Provides field and lab data with specific optimization suggestions</li>
  <li>Google Search Console: Offers a dedicated Core Web Vitals report based on real-user Chrome data</li>
  <li>Lighthouse: Allows detailed performance auditing in development environments</li>
  <li>Chrome DevTools: Provides real-time performance measurements and debugging capabilities</li>
  <li>Web Vitals JavaScript library: Enables custom tracking and reporting of Core Web Vitals metrics</li>
</ul>

<h2>The Future of Performance Metrics</h2>
<p>As web technologies evolve, so do performance metrics. Google continues to refine Core Web Vitals to better reflect actual user experience. Staying informed about these changes and maintaining a performance-focused development approach will ensure your site remains competitive in search rankings while delivering the best possible experience to visitors.</p>

<p>Remember that Core Web Vitals optimization is not a one-time task but an ongoing process requiring regular monitoring and refinement as your site evolves and user expectations increase.</p>
                """,
                'category': 'Technical SEO'
            },
            {
                'title': 'The Complete Guide to Content Optimization',
                'excerpt': 'Learn how to optimize your content for both search engines and human readers with this comprehensive guide.',
                'content': """
<p>Content optimization is the art and science of creating web content that satisfies both search engine algorithms and human readers. This comprehensive guide covers everything you need to know to create high-performing content that ranks well and engages your audience effectively.</p>

<h2>Understanding the Dual Audience</h2>
<p>Successful content must serve two masters: search engines that determine visibility and human readers who determine engagement, conversions, and business value. Modern content optimization requires balancing technical SEO requirements with quality writing that resonates with your target audience.</p>

<h2>Research and Planning</h2>

<h3>Keyword Research</h3>
<p>Effective content optimization begins with identifying the right keywords and topics to target. This process involves:</p>

<ul>
  <li><strong>Search intent analysis:</strong> Understanding what users are actually looking for when they use specific search terms</li>
  <li><strong>Competitive analysis:</strong> Examining what content already ranks for your target keywords</li>
  <li><strong>Volume and difficulty assessment:</strong> Balancing search volume with keyword difficulty to find valuable opportunities</li>
  <li><strong>Long-tail keyword identification:</strong> Targeting specific phrases with lower competition but high relevance</li>
</ul>

<h3>Content Mapping</h3>
<p>Create a strategic content map that aligns with your audience's journey:</p>

<ul>
  <li>Awareness stage: Educational content that addresses broad questions</li>
  <li>Consideration stage: Comparative content that explores solutions</li>
  <li>Decision stage: Conversion-focused content that facilitates action</li>
</ul>

<h2>On-Page Optimization Techniques</h2>

<h3>Title Tag Optimization</h3>
<p>Create compelling, keyword-rich titles that:</p>
<ul>
  <li>Include the primary keyword (ideally near the beginning)</li>
  <li>Stay under 60 characters to avoid truncation in search results</li>
  <li>Communicate clear value to potential readers</li>
  <li>Use power words that encourage clicks</li>
</ul>

<h3>Meta Description Crafting</h3>
<p>While not a direct ranking factor, well-written meta descriptions improve click-through rates:</p>
<ul>
  <li>Include your primary keyword naturally</li>
  <li>Keep within 150-160 characters</li>
  <li>Include a compelling call to action</li>
  <li>Accurately summarize the page content</li>
</ul>

<h3>Header Structure</h3>
<p>Properly structured headers help both search engines and readers understand your content:</p>
<ul>
  <li>Use H1 for the main title (only one per page)</li>
  <li>Implement H2s for major section headings</li>
  <li>Use H3s and H4s for subsections</li>
  <li>Include relevant keywords in headers naturally</li>
  <li>Create a logical, hierarchical structure</li>
</ul>

<h3>Content Structure</h3>
<p>Organize content for maximum readability and comprehension:</p>
<ul>
  <li>Begin with a compelling introduction that states what readers will learn</li>
  <li>Use short paragraphs (3-4 sentences maximum)</li>
  <li>Incorporate bulleted and numbered lists for scannable information</li>
  <li>Include relevant subheadings every 200-300 words</li>
  <li>End with a conclusion that summarizes key points and provides next steps</li>
</ul>

<h2>Content Quality Factors</h2>

<h3>E-A-T Principles</h3>
<p>Google evaluates content based on Expertise, Authoritativeness, and Trustworthiness:</p>
<ul>
  <li><strong>Demonstrate expertise:</strong> Show deep knowledge of your subject through comprehensive coverage</li>
  <li><strong>Build authority:</strong> Include credentials, cite authoritative sources, and link to relevant research</li>
  <li><strong>Establish trust:</strong> Provide accurate, up-to-date information with proper attribution</li>
</ul>

<h3>Content Depth and Comprehensiveness</h3>
<p>Modern SEO rewards content that thoroughly addresses user needs:</p>
<ul>
  <li>Cover topics comprehensively rather than superficially</li>
  <li>Answer related questions users might have</li>
  <li>Provide actionable information and practical examples</li>
  <li>Update content regularly to maintain relevance</li>
</ul>

<h3>Readability and Engagement</h3>
<p>Content must be accessible and engaging to perform well:</p>
<ul>
  <li>Write at an appropriate reading level for your audience (aim for grades 7-9 for general content)</li>
  <li>Use active voice and conversational tone</li>
  <li>Break up text with visual elements</li>
  <li>Include stories and examples that illustrate key points</li>
  <li>Eliminate jargon unless writing for a specialized audience</li>
</ul>

<h2>Visual Content Optimization</h2>

<h3>Image Optimization</h3>
<p>Visual elements require specific optimization techniques:</p>
<ul>
  <li>Use descriptive, keyword-rich file names</li>
  <li>Complete alt text for accessibility and SEO</li>
  <li>Compress images for faster loading</li>
  <li>Implement responsive image techniques</li>
  <li>Consider image sitemaps for large sites</li>
</ul>

<h3>Video Optimization</h3>
<p>For video content:</p>
<ul>
  <li>Include transcripts for accessibility and indexing</li>
  <li>Create descriptive titles and descriptions</li>
  <li>Add chapters or timestamps for longer videos</li>
  <li>Embed videos properly with structured data</li>
</ul>

<h2>Technical Content Optimization</h2>

<h3>Schema Markup</h3>
<p>Implement structured data to enhance how your content appears in search results:</p>
<ul>
  <li>Article schema for blog posts</li>
  <li>FAQ schema for question-and-answer content</li>
  <li>How-to schema for instructional content</li>
  <li>Product schema for e-commerce pages</li>
</ul>

<h3>Mobile Optimization</h3>
<p>Ensure content performs well on all devices:</p>
<ul>
  <li>Use responsive design principles</li>
  <li>Test readability on small screens</li>
  <li>Ensure tap targets are appropriately sized</li>
  <li>Minimize interstitials that interrupt the reading experience</li>
</ul>

<h2>Content Performance Measurement</h2>
<p>Establish metrics to evaluate content effectiveness:</p>

<ul>
  <li><strong>Search performance:</strong> Rankings, organic traffic, and click-through rates</li>
  <li><strong>Engagement metrics:</strong> Time on page, bounce rate, and scroll depth</li>
  <li><strong>Conversion metrics:</strong> Lead generation, sales, and goal completions</li>
  <li><strong>Social metrics:</strong> Shares, comments, and amplification</li>
</ul>

<p>Use these insights to continually refine your optimization strategy, updating underperforming content and replicating successful approaches.</p>

<h2>The Future of Content Optimization</h2>
<p>As search technology evolves, content optimization continues to change. Emerging trends include:</p>

<ul>
  <li><strong>AI-driven content analysis:</strong> Using machine learning to identify optimization opportunities</li>
  <li><strong>Voice search optimization:</strong> Adapting content for conversational queries</li>
  <li><strong>Multimodal search:</strong> Optimizing for searches that combine text, images, and voice</li>
  <li><strong>User interaction signals:</strong> Creating content that encourages meaningful engagement</li>
</ul>

<p>The most effective content optimization strategy embraces these technological advances while remaining focused on creating genuine value for users. By balancing technical best practices with high-quality, user-focused content, you can achieve sustainable organic search success.</p>
                """,
                'category': 'Content Marketing'
            }
        ]
        
        # Create posts
        created_count = 0
        for post_data in posts:
            # Get or create category
            category_name = post_data['category']
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={'slug': slugify(category_name)}
            )
            
            # Check if post already exists
            slug = slugify(post_data['title'])
            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(self.style.WARNING(f'Post with slug "{slug}" already exists, skipping...'))
                continue
            
            # Create post
            post = Post(
                title=post_data['title'],
                slug=slug,
                author=user,
                category=category,
                content=post_data['content'],
                excerpt=post_data['excerpt'],
                status='published',
                published_date=timezone.now()
            )
            
            # Try to add a featured image
            try:
                # Get a random placeholder image
                image_id = random.randint(1, 1000)
                response = requests.get(f'https://picsum.photos/800/450?random={image_id}', timeout=10)
                if response.status_code == 200:
                    # Save the image
                    file_name = f'blog_post_{slug}.jpg'
                    content_file = ContentFile(response.content)
                    post.featured_image.save(file_name, content_file, save=False)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error adding featured image: {e}'))
            
            # Save the post
            post.save()
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Successfully created post: {post.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} blog posts'))
    
    def _ensure_categories(self):
        """Create default categories if they don't exist"""
        default_categories = [
            'SEO Techniques',
            'Content Marketing',
            'Technical SEO',
            'Link Building',
            'Digital Marketing',
            'Analytics'
        ]
        
        categories = []
        for name in default_categories:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name)}
            )
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))
            
        return categories 