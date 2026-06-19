import HeroSection from "@/components/hero-section";
import Features from "@/components/features-3";
import Agenda from "@/components/agenda";
import CapabilitiesGrid from "@/components/capabilities-grid";
import CallToAction from "@/components/call-to-action";

export default function Home() {
    return (
        <>
            <HeroSection/>
            <Agenda/>
            <CapabilitiesGrid/>
            <Features/>
            <CallToAction/>
        </>
    )
}
